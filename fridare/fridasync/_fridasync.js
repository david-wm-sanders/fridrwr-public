// Set a general exception handler here to help with development
Process.setExceptionHandler(details => {
  const m = { type: "log", level: "process_exception", payload: details };
  _send(JSON.stringify(m), null);
  // send(details);
});

rpc.exports.fridaVersion = function () {
  return Frida.version;
}

rpc.exports.fridaHeapSize = function () {
  return Frida.heapSize;
}

rpc.exports.fridaScriptRuntime = function () {
  return Script.runtime;
}

rpc.exports.pid = function () {
  return Process.id;
}

rpc.exports.arch = function () {
  return Process.arch;
}

rpc.exports.platform = function () {
  return Process.platform;
}

rpc.exports.pageSize = function () {
  return Process.pageSize;
}

rpc.exports.pointerSize = function () {
  return Process.pointerSize;
}

rpc.exports.codeSigningPolicy = function () {
  return Process.codeSigningPolicy;
}

rpc.exports.isDebuggerAttached = function () {
  return Process.isDebuggerAttached();
}

rpc.exports.getCurrentThreadId = function () {
  return Process.getCurrentThreadId();
}

rpc.exports.enumerateThreads = function () {
  return Process.enumerateThreads();
}

// TODO: Process.findModuleByAddress
// TODO: Process.getModuleByAddress
// TODO: Process.findModuleByName

rpc.exports.getModuleByName = function (name) {
  return Process.getModuleByName(name);
}

rpc.exports.enumerateModules = function () {
  return Process.enumerateModules();
};

// TODO: Process.findRangeByAddress
// TODO: Process.getRangeByAddress
// TODO: Process.enumerateRanges

// rpc.exports.enumerateMallocRanges = function () {
//   return Process.enumerateMallocRanges();
// }


rpc.exports.scanSync = function (address, size, pattern) {
  var address_ptr = ptr(address);
  return Memory.scanSync(address_ptr, size, pattern);
}

rpc.exports.parseInstruction = function (target_address) {
  var target_address_ptr = ptr(target_address);
  return Instruction.parse(target_address_ptr);
}
