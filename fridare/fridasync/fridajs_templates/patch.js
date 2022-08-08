function _log_debug(message) {
  const m = { type: "log", level: "debug", payload: message };
  // use the internal send (ref: https://github.com/frida/frida-gum/blob/master/bindings/gumjs/runtime/console.js)
  // in order to pass custom log level "debug"
  _send(JSON.stringify(m), null);
}

function _log_info(message) {
  console.log(message);
}

function _log_warn(message) {
  console.warn(message);
}

function _log_error(message) {
  console.error(message);
}


class Patch {
  constructor(name, module_name, target_pattern, vars_spec) {
    // the name of the patch - used for fridrwr.{apply,clear}_patch etc
    this.name = name;
    // the name of the module e.g. rwr_game.exe | OgreMain.dll
    this.module_name = module_name;
    // the pattern for Memory.scanSync
    this.target_pattern = target_pattern;
    // the spec for the vars that the patch should init/allocate memory for and then pass into the constructor defined
    // patch function writer xD
    this.vars_spec = vars_spec;

    // init to starting values
    this.is_setup = false;
    this.target = null;
    this.target_bytes = [];

    // setup patch vars from vars_spec
    this.vars = new Map();
    for (let v of this.vars_spec) {
      var vmem = Memory.alloc(v.size);
      _log_debug("Patch '" + this.name + "' init allocated " + v.size + " bytes for '" + v.name + "' @ " + vmem);
      this.vars.set(v.name, { mem: vmem, type: v.type, size: v.size, default: v.default });
      this.writePatchVar(v.name, v.default);
    }
  }

  writePatchVar(var_name, value) {
    _log_debug("Patch '" + this.name + "' write patch var: " + var_name + " = " + value);
    // if a var of this name doesn't exist in the vars Map, log an error and fail fast
    if (!this.vars.has(var_name)) {
      _log_error("Patch '" + this.name + "' has no var '" + var_name + "', can't write to var that doesn't exist :/");
      return false;
    }
    var v = this.vars.get(var_name);
    switch (v.type) {
      case "float":
        var f = parseFloat(value);
        Memory.writeFloat(v.mem, f);
        break;
      // etc etc: u8, s16, u16, s32, u32, short, ushort, int, uint, float, double, s64, u64, long, ulong
      default:
        _log_error("Patch var type '" + v.type +"' not handled...");
        return false;
    }
    return true;
  }

  _find() {
    var m = Process.getModuleByName(this.module_name);
    var hits = Memory.scanSync(m.base, m.size, this.target_pattern);
    if (hits.length == 0) {
      _log_error("Patch '" + this.name + "', searching for '" + this.target_pattern + "', matched nothing");
      return null;
    } else if (hits.length > 1) {
      _log_warn("Patch '" + this.name + "', searching for '" + this.target_pattern + "', matched " +
                 "more than once, pattern must be unique in search space");
      return null;
    } else {
      _log_info("Patch '" + this.name + "', searching for '" + this.target_pattern + "', matched: " +
                JSON.stringify(hits));
      return hits[0];
    }
  }

  setup() {
    _log_info("Setting up patch '" + this.name + "'...");
    var target = this._find();
    if (target === null) {
      // failed to find target, setup failed, ret false;
      _log_error("Patch '" + this.name + "' failed to find target pattern '" + this.target_pattern + "' :/")
      return false;
    }
    this.target = target;
    _log_debug("Patch '" + this.name + "' found target @ " + JSON.stringify(this.target));
    // hmmm, this seems to create an ArrayBuffer as a biew on the memory where what we actually want is an array of bytes
    // this.target_bytes = this.target.address.readByteArray(this.target.size);
    // from the start of the matched pattern target, read byte by byte into this.target_bytes
    // this is used instead of readByteArray because we want a copy of the data, rather than an ArrayBuffer view
    // this.target_bytes will be used by patch.clear() to unapply jmp/nop at the target location (by rewriting original bytes)
    for (let offset = 0; offset < this.target.size; offset++) {
      this.target_bytes.push(ptr(this.target.address).add(offset).readU8());
    }
    var hex_bytes = [];
    for (let i of this.target_bytes) {
      hex_bytes.push(i.toString(16).toUpperCase());
    }
    _log_debug("Patch '" + this.name + "' target_bytes = " + JSON.stringify(hex_bytes));
    return true;
  }

  apply() {
    if (this.is_setup === false) {
      // the patch is not setup, do it now!
      _log_debug("Patch '" + this.name + "' not setup, setting up patch now...");
      var setup_result = this.setup();
      // fail if the setup_result is false, i.e. setup failed
      if (setup_result === false) return false;
      this.is_setup = true;
      return true;
    }
    else if (this.is_setup === true) {
      _log_debug("Patch '" + this.name + "' patch already setup, reusing setup...");
      // once patch basics are setup, it is left to the subclass to implement the patch application specifics
      return true;
    }
    else return false;
  }

  clear() {
    _log_error("Patch '" + this.name + "' clear method must be implemented by subclass");
    return false;
  }
}

{% block patch_extension %}{% endblock patch_extension %}

function _putPointer(cw, var_pointer) {
  // get the current code addr ptr
  var a = cw.code;
  // put an address ptr length of bytes (4) in to move the codewriter forwards
  cw.putBytes([0x00, 0x00, 0x00, 0x00]);
  // overwrite the address with the actual address
  a.writePointer(var_pointer);
  cw.flush();
}

{% block patch_constructor %}{% endblock patch_constructor %}

rpc.exports.apply = function () {
    return {{ name }}_patch.apply();
}

rpc.exports.clear = function () {
    return {{ name }}_patch.clear();
}
