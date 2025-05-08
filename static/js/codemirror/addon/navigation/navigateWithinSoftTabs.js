(function(mod) {
  if (typeof exports == "object" && typeof module == "object") // CommonJS
    mod(require("../../lib/codemirror"));
  else if (typeof define == "function" && define.amd) // AMD
    define(["../../lib/codemirror"], mod);
  else // Plain browser env
    mod(CodeMirror);
})(function(CodeMirror) {
  "use strict";

  var LEFT_KEY = 37;
  var RIGHT_KEY = 39;

  var emptyRegex = /^\s*$/;

  function repeatStringNumTimes(string, times) {
    if (times > 0)
      return string.repeat(times);
    else
      return "";
  }

  function insertSmartTab(cm) {
    if (cm.getOption('indentWithTabs')) {
      cm.replaceSelection("\t", "end", "+input");
    } else {
      var cursor = cm.getCursor();
      var tabSize = cm.getOption('tabSize');
      var numSpaces = (Math.floor(cursor.ch / tabSize) + 1) * tabSize - cursor.ch;
      cm.replaceSelection(repeatStringNumTimes(" ", numSpaces), "end", "+input");
    }
  }

  function smartTab(cm) {
    cm.operation(function (){
      if (cm.somethingSelected()) {
        cm.indentSelection("add");
      } else {
        insertSmartTab(cm);
      }
    });
  }

  function smartDelete(cm) {
    cm.operation(function (){
      var sel = cm.doc.sel, doc = cm.doc;
      if (sel.somethingSelected()) {
        doc.replaceSelection("", null, "+delete");
      } else {
        var cursor = cm.getCursor();
        var tabSize = cm.getOption('tabSize');
        var end = cm.findPosH(cursor, tabSize, "column");
        if (end && end.line === cursor.line) {
          var word = cm.getRange(cursor, end);
          if ((cursor.ch % tabSize) === 0 && emptyRegex.test(word)) {
            cm.doc.replaceRange("", cursor, end);
          } else {
            cm.deleteH(1, "char");
          }
        } else {
          cm.deleteH(1, "char");
        }
      }
    });
  }

  function smartBackspace(cm) {
    cm.operation(function (){
      var sel = cm.doc.sel, doc = cm.doc;
      if (sel.somethingSelected()) {
        doc.replaceSelection("", null, "+delete");
      } else {
        var cursor = cm.getCursor();
        var tabSize = cm.getOption('tabSize');
        var start = {line: cursor.line, ch: cursor.ch - tabSize};
        var word = cm.getRange(start, cursor);
        if (cursor.ch >= tabSize && (cursor.ch % tabSize) === 0 && emptyRegex.test(word)) {
          cm.doc.replaceRange("", start, cursor);
        } else {
          cm.deleteH(-1, "char");
        }
      }
    });
  }

  var prevExtraKeys = null;
  CodeMirror.defineOption("navigateWithinSoftTabs", null, function (cm, val, old) {
    var prev = old == CodeMirror.Init ? null : old;
    if (val == prev) return
    if (prev) {
      // turn off navigation
      cm.off("keydown", onKeyDown);
      cm.off("mousedown", onMouseDown);
      cm.off('cursorActivity', cursorActivity);
      cm.state.navigateWithinSoftTabs = {};
      cm.setOption("extraKeys", prevExtraKeys);
    }
    if (val) {
      // turn on navigation
      cm.on("keydown", onKeyDown);
      cm.on("mousedown", onMouseDown);
      cm.on('cursorActivity', cursorActivity);
      cm.state.navigateWithinSoftTabs = {
        tabSize: null,
        startPos: null,
        direction: null
      };
      prevExtraKeys = cm.getOption("extraKeys");
      cm.setOption("extraKeys", {
        Tab: smartTab,
        Delete: smartDelete,
        Backspace: smartBackspace
      });
    }
  });

  function update(cmInstance) {
    var state = cmInstance.state.navigateWithinSoftTabs;
    var event = state.lastEvent;
    if (!event) {
      return;
    }
    var isSelection = cmInstance.somethingSelected();
    if (event.which !== LEFT_KEY && event.which !== RIGHT_KEY) {
      return;
    }
    var start = state.startPos;
    var end = cmInstance.findPosH(start, state.direction, "column");
    var range = "";
    if (start.ch % state.tabSize !== 0) {
      return;
    }
    if (state.direction >= 0) {
      range = cmInstance.doc.getRange(start, end);
    } else {
      range = cmInstance.doc.getRange(end, start);
    }
    var canJump = range.split(" ").length - 1 === state.tabSize;
    if (canJump) {
      event.preventDefault();
      if (isSelection) {
        cmInstance.extendSelection(end);
      } else {
        cmInstance.setCursor(end);
      }
    }
  }

  function cursorActivity(cmInstance) {
    cmInstance.operation(function (){ update(cmInstance); });
  }

  function onKeyDown(cmInstance, event) {
    var state = cmInstance.state.navigateWithinSoftTabs;
    state.tabSize = cmInstance.options.tabSize;
    state.direction = state.tabSize;
    if (event.which === LEFT_KEY || event.which === RIGHT_KEY) {
      if (event.which === LEFT_KEY) {
        state.direction = -(state.tabSize);
      }
      state.startPos = cmInstance.getCursor();
      state.lastEvent = event;
    } else {
      state.lastEvent = null;
      return;
    }
  }

  function onMouseDown(cmInstance, event) {
    var state = cmInstance.state.navigateWithinSoftTabs;
    state.lastEvent = null;
  }
});