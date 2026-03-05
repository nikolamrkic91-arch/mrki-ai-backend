; Mrki syntax highlighting for Zed

; Keywords
"prompt" @keyword
"context" @keyword
"model" @keyword
"temperature" @keyword
"max_tokens" @keyword

; Strings
(string) @string
(quoted_string) @string

; Comments
(comment) @comment

; Numbers
(number) @number

; Booleans
(true) @boolean
(false) @boolean

; Variables
(variable) @variable

; Functions
(function_call
  name: (identifier) @function)

; Operators
[
  "="
  "+"
  "-"
  "*"
  "/"
  "=="
  "!="
  "<"
  ">"
  "<="
  ">="
] @operator

; Punctuation
["{" "}"] @punctuation.bracket
["[" "]"] @punctuation.bracket
["(" ")"] @punctuation.bracket
["," "."] @punctuation.delimiter
