{% extends "patch.js" %}

{% block patch_extension %}
class NopPatch extends Patch {
  constructor(name, module_name, target_pattern, nop_offset, nop_length) {
    super(name, module_name, target_pattern, []);
    this.nop_offset = nop_offset;
    this.nop_length = nop_length;
  }

  setup() {
    // call the superclass setup to get this.target and this.target_bytes setup
    var r = super.setup();
    // if this returned value is false, super.setup() has failed and we can't go on, ret false;
    if (r === false) {
      _log_error("NopPatch '" + this.name + "' super.setup() failed :/");
      return false;
    }
    // no further setup required here atm
    return true;
  }

  apply() {
    var r = super.apply();

    // if this returned value is false, super.apply() has failed and we can't go on, ret false;
    if (r === false) {
      _log_error("NopPatch '" + this.name + "' super.apply() failed :/");
      return false;
    }

    // TODO: make a codewriter from nop_offset and write nop_length nops to it
    Memory.patchCode(this.target.address.add(this.nop_offset), this.target.size - this.nop_offset, code => {
      const cw = new X86Writer(code, { pc: this.target.address.add(this.nop_offset)});
      cw.putNopPadding(this.nop_length);
      cw.flush();
    });
    return true;
  }

  clear() {
    // super.clear() // not cleared at Patch level as there is just a blank filler func there atm
    _log_debug("NopPatch '" + this.name + "' is clearing patch by restoring original bytes at target site...")
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
{% endblock patch_extension %}

{% block patch_constructor %}
var {{ name }}_patch = new NopPatch("{{ name }}", "{{ module_name }}",
                                    "{{ target_pattern }}",
                                    {{ nop_offset }}, {{ nop_length }})
{% endblock patch_constructor %}
