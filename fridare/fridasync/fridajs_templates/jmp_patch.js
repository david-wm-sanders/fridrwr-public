{% extends "patch.js" %}

{% block patch_extension %}
class JmpPatch extends Patch {
  constructor(name, module_name, target_pattern, vars_spec,
              relocate_target, patch_mem_size, return_offset, cw_patch_func) {
    super(name, module_name, target_pattern, vars_spec)
    this.relocate_target = relocate_target;
    // size of the memory, to allocate, for code to be written into
    this.patch_mem_size = patch_mem_size;
    // the offset of the address to jmp to post patch relative to target site base
    this.return_offset = return_offset;
    // the constructor provided function that does the patch-specific code writing
    this.cw_patch_func = cw_patch_func;
    // set up patch memory
    this.patch_memory = null;
    // allocate some memory that we can write the patch code into later
    this.patch_memory = Memory.alloc(this.patch_mem_size);
    _log_debug("JmpPatch '" + this.name + "' allocated patch memory @ " + this.patch_memory);
    // set the protection on the allocated memory to make sure it can be executed later
    Memory.protect(this.patch_memory, this.patch_mem_size, "rwx");
  }

  setup() {
    // call the superclass setup to get this.target and this.target_bytes setup
    var r = super.setup();
    // if this returned value is false, super.setup() has failed and we can't go on, ret false;
    if (r === false) {
      _log_error("JmpPatch '" + this.name + "' super.setup() failed :/");
      return false;
    }
    // create a codewriter pointed at this.patch_memory start
    const cw = new X86Writer(this.patch_memory, { pc: this.patch_memory });
    // if this.relocate_target, patch specifies that the matched target bytes should be written at start of patch mem
    if (this.relocate_target === true) {
      for (let b of this.target_bytes) {
        cw.putU8(b);
      }
      cw.flush();
    }

    // run the user supplied function to write the custom patch code
    this.cw_patch_func(cw, this.vars);
    // write the jmp to return back to the normal program flow
    cw.putJmpAddress(this.target.address.add(this.return_offset));
    cw.flush();
    // DEBUG: check
    _log_debug("JmpPatch '" + this.name + "' hexdump of patch memory at end of setup:\n" +
                hexdump(this.patch_memory, { offset: 0, length: this.patch_mem_size, header: true, ansi: false}));

    return true;
  }

  apply () {
    var r = super.apply();

    // if this returned value is false, super.apply() has failed and we can't go on, ret false;
    if (r === false) {
      _log_error("JmpPatch '" + this.name + "' super.apply() failed :/");
      return false;
    }
    // TODO: really need to add better guards here in future, we need target_pattern to return targets of size
    // >= 5 bytes in order to have enough space to write a 1 byte JMP + 4 byte address at the patch target site
    // for now, let's just try it...
    var nop_sled_length = this.target.size - 5;
    _log_debug("JmpPatch '" + this.name +
               "' will need " + nop_sled_length + " nop(s) after jmp @ '" + this.target.address + "'")
    if (nop_sled_length < 0) {
      _log_error("JmpPatch '" + this.name +
                 "' does not have enough space to write a jmp @ '" + this.target.address + "'");
      return false;
    }
    // hmm ok, now write the jmp at the patch target site
    Memory.patchCode(this.target.address, this.target.size, code => {
      const cw = new X86Writer(code, { pc: this.target.address});
      cw.putJmpAddress(this.patch_memory);
      cw.putNopPadding(nop_sled_length);
      cw.flush();
    });
    return true;
  }

  clear() {
    // super.clear() // not cleared at Patch level as there is just a blank filler func there atm
    _log_debug("JmpPatch '" + this.name + "' is clearing patch by restoring original bytes at target site...")
    Memory.patchCode(this.target.address, this.target.size, code => {
      const cw = new X86Writer(code, { pc: this.target.address });
      for (let b of this.target_bytes) {
        cw.putU8(b);
      }
      cw.flush();
    });
    return true;
  }
}

// x86 register codes...
const X86_REG = {ESP: 0x24};

// rwr uses a lot of x87 floating point instructions that patches need to be able to write
// might be possible to integrate a lot of this into a subclass of X86Writer
// (alternatively, keystone-engine create the bytecode and create patches from fridrwr)
// discovered for X86_32_INTEL using CE memory viewer and Instruction.parse
// indicated in the comments is the data/byte(s) operands that must be written immediately after the opcode
// warning: incomplete operands information! (best to use debugger assistance here)
// in cases where the term "reversed offset" is used this means: esp+00000124, reversed offset is 24 01 00 00
const X86_32_OP = {FMUL_DWORDPTR_EAX: [0xD8, 0x08],               // > -
                   FADD_DWORDPTR_ESI_OFFSET: [0xD8, 0x46],        // > 1-byte offset
                   FMUL_DWORDPTR_EAX_OFFSET: [0xD8, 0x48],
                   FMUL_DWORDPTR_REG_OFFSET: [0xD8, 0x4C],        // > 1-byte register code, 1-byte offset
                   FMUL_DWORDPTR_ESI_OFFSET: [0xD8, 0x4E],        // > 1-byte offset
                   FCOMP_DWORDPTR_ECX_OFFSET: [0xD8, 0x59],
                   FSUB_DWORDPTR_ESI_OFFSET: [0xD8, 0x66],        // > 1-byte offset
                   FMUL_DWORDPTR_REG_OFFSET_FULL: [0xD8, 0x8C],   // > 1-byte register code, 4-byte reversed offset
                   FCOMP_DWORDPTR_REG_OFFSET_FULL: [0xD8, 0x9C],  // > 1-byte register code, 4-byte reversed offset
                   FSUB_DWORDPTR_ESI_OFFSET_FULL: [0xD8, 0xA6],   // > 4-byte reversed offset
                   FLD_DWORDPTR_ADDR: [0xD9, 0x05],
                   FSTP_DWORDPTR_REG: [0xD9, 0x1C],               // > 1-byte register code
                   FLD_DWORDPTR_EAX_OFFSET: [0xD9, 0x40],         // > 1-byte offset
                   FLD_DWORDPTR_ECX_OFFSET: [0xD9, 0x41],
                   FLD_DWORDPTR_REG_OFFSET: [0xD9, 0x44],         // > 1-byte register code, 1-byte offset
                   FLD_DWORDPTR_ESI_OFFSET: [0xD9, 0x46],         // > 1-byte offset
                   FST_DWORDPTR_EAX_OFFSET: [0xD9, 0x50],
                   FST_DWORDPTR_REG_OFFSET: [0xD9, 0x54],         // > 1-byte register code, 1-byte offset
                   FST_DWORDPTR_ESI_OFFSET: [0xD9, 0x56],
                   FSTP_DWORDPTR_EAX_OFFSET: [0xD9, 0x58],
                   FSTP_DWORDPTR_EBX_OFFSET: [0xD9, 0x5B],
                   FSTP_DWORDPTR_ECX_OFFSET: [0xD9, 0x59],
                   FSTP_DWORDPTR_REG_OFFSET: [0xD9, 0x5C],        // > 1-byte register code, 1-byte offset
                   FSTP_DWORDPTR_ESI_OFFSET: [0xD9, 0x5E],        // > 1-byte offset
                   FSTP_DWORDPTR_ESI_OFFSET_FULL: [0xD9, 0x9E],   // > 4-byte reversed offset
                   FCHS: [0xD9, 0xE0],
                   FLD1: [0xD9, 0xE8],
                   FLDZ: [0xD9, 0xEE]
                 };
{% endblock patch_extension %}

{% block patch_constructor %}
var {{ name }}_patch = new JmpPatch("{{ name }}", "{{ module_name }}",
                                    "{{ target_pattern }}", {{ vars_spec }}, {{ relocate_target }},
                                    {{ patch_mem_size }}, {{ return_offset }},
                                    (cw, vars) => { {{ cw_patch_func }}});
{% endblock patch_constructor %}
