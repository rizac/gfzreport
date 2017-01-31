Ace rst highlighter has been modified to account for rst fields highlights

The file modified is in ./ace-build/mode-rst.js
The original file has been renamed to ./ace-build/mode-rst-default.js

The new highlighter implements some regexp for recognizing field NAMES. Inside rst directives, the
whole line :fieldname: fieldbody is highlighted, because highlighting only the name broke
the whole directive block highlights and i didn't figure out some easy hack to avoid it

If you want to edit the file, have a look first at:
https://github.com/ajaxorg/ace/blob/master/lib/ace/mode/rst_highlight_rules.js

If you want to CHECK my modifications, search for the string "ADDED BY ME"

A copy of the MODIFIED file content is the last line below because if we update ./ace-build
and find out that our rst syntax highlighter is lost, then redo the procedure:
copy ./ace-build/mode-rst.js into ./ace-build/mode-rst-default.js
and copy-paste the line below into ./ace-build/mode-rst.js:

ace.define("ace/mode/rst_highlight_rules",["require","exports","module","ace/lib/oop","ace/lib/lang","ace/mode/text_highlight_rules"],function(e,t,n){"use strict";var r=e("../lib/oop"),i=e("../lib/lang"),s=e("./text_highlight_rules").TextHighlightRules,o=function(){var e={title:"markup.heading",list:"markup.heading",table:"constant",directive:"keyword.operator",entity:"string",link:"markup.underline.list",bold:"markup.bold",italic:"markup.italic",literal:"support.function",comment:"comment"},t="(^|\\s|[\"'(<\\[{\\-/:])",n="(?:$|(?=\\s|[\\\\.,;!?\\-/:\"')>\\]}]))";this.$rules={start:[{token:e.title,regex:"(^)([\\=\\-`:\\.'\"~\\^_\\*\\+#])(\\2{2,}\\s*$)"},{token:["text",e.directive,e.literal],regex:"(^\\s*\\.\\. )([^: ]+::)(.*$)",next:"codeblock"},{token:e.directive,regex:"::$",next:"codeblock"},{token:[e.entity,e.link],regex:"(^\\.\\. _[^:]+:)(.*$)"},{token:[e.entity,e.link],regex:"(^__ )(https?://.*$)"},{token:e.entity,regex:"^\\.\\. \\[[^\\]]+\\] "},{token:e.comment,regex:"^\\.\\. .*$",next:"comment"},/*ADDED BY ME*/{token:"markup.keyword",regex:"\\:(.*?)\\: "},/**/{token:e.list,regex:"^\\s*[\\*\\+-] "},{token:e.list,regex:"^\\s*(?:[A-Za-z]|[0-9]+|[ivxlcdmIVXLCDM]+)\\. "},{token:e.list,regex:"^\\s*\\(?(?:[A-Za-z]|[0-9]+|[ivxlcdmIVXLCDM]+)\\) "},{token:e.table,regex:"^={2,}(?: +={2,})+$"},{token:e.table,regex:"^\\+-{2,}(?:\\+-{2,})+\\+$"},{token:e.table,regex:"^\\+={2,}(?:\\+={2,})+\\+$"},{token:["text",e.literal],regex:t+"(``)(?=\\S)",next:"code"},{token:["text",e.bold],regex:t+"(\\*\\*)(?=\\S)",next:"bold"},{token:["text",e.italic],regex:t+"(\\*)(?=\\S)",next:"italic"},{token:e.entity,regex:"\\|[\\w\\-]+?\\|"},{token:e.entity,regex:":[\\w-:]+:`\\S",next:"entity"},{token:["text",e.entity],regex:t+"(_`)(?=\\S)",next:"entity"},{token:e.entity,regex:"_[A-Za-z0-9\\-]+?"},{token:["text",e.link],regex:t+"(`)(?=\\S)",next:"link"},{token:e.link,regex:"[A-Za-z0-9\\-]+?__?"},{token:e.link,regex:"\\[[^\\]]+?\\]_"},{token:e.link,regex:"https?://\\S+"},{token:e.table,regex:"\\|"}],codeblock:[/*ADDED BY ME*/{token:"markup.keyword",regex:"^\\s+(\\:.*?\\:) (.*?)$",next:"codeblock"},/**/{token:e.literal,regex:"^ +.+$",next:"codeblock"},{token:e.literal,regex:"^$",next:"codeblock"},{token:"empty",regex:"",next:"start"}],code:[{token:e.literal,regex:"\\S``"+n,next:"start"},{defaultToken:e.literal}],bold:[{token:e.bold,regex:"\\S\\*\\*"+n,next:"start"},{defaultToken:e.bold}],italic:[{token:e.italic,regex:"\\S\\*"+n,next:"start"},{defaultToken:e.italic}],entity:[{token:e.entity,regex:"\\S`"+n,next:"start"},{defaultToken:e.entity}],link:[{token:e.link,regex:"\\S`__?"+n,next:"start"},{defaultToken:e.link}],comment:[{token:e.comment,regex:"^ +.+$",next:"comment"},{token:e.comment,regex:"^$",next:"comment"},{token:"empty",regex:"",next:"start"}]}};r.inherits(o,s),t.RSTHighlightRules=o}),ace.define("ace/mode/rst",["require","exports","module","ace/lib/oop","ace/mode/text","ace/mode/rst_highlight_rules"],function(e,t,n){"use strict";var r=e("../lib/oop"),i=e("./text").Mode,s=e("./rst_highlight_rules").RSTHighlightRules,o=function(){this.HighlightRules=s};r.inherits(o,i),function(){this.type="text",this.$id="ace/mode/rst"}.call(o.prototype),t.Mode=o})



