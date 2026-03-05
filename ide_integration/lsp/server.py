#!/usr/bin/env python3
"""
Mrki Language Server Protocol (LSP) Implementation
"""

import argparse
import asyncio
import json
import logging
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union

# LSP types
@dataclass
class Position:
    line: int
    character: int
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'Position':
        return cls(line=d.get('line', 0), character=d.get('character', 0))
    
    def to_dict(self) -> Dict:
        return {'line': self.line, 'character': self.character}


@dataclass
class Range:
    start: Position
    end: Position
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'Range':
        return cls(
            start=Position.from_dict(d.get('start', {})),
            end=Position.from_dict(d.get('end', {}))
        )
    
    def to_dict(self) -> Dict:
        return {'start': self.start.to_dict(), 'end': self.end.to_dict()}


@dataclass
class TextDocumentItem:
    uri: str
    languageId: str
    version: int
    text: str


@dataclass
class TextDocumentIdentifier:
    uri: str


@dataclass
class VersionedTextDocumentIdentifier:
    uri: str
    version: int


@dataclass
class TextDocumentContentChangeEvent:
    range: Optional[Range]
    rangeLength: Optional[int]
    text: str


@dataclass
class CompletionItem:
    label: str
    kind: Optional[int] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insertText: Optional[str] = None
    insertTextFormat: Optional[int] = None
    sortText: Optional[str] = None
    filterText: Optional[str] = None
    preselect: Optional[bool] = None
    
    def to_dict(self) -> Dict:
        result = {'label': self.label}
        if self.kind is not None:
            result['kind'] = self.kind
        if self.detail is not None:
            result['detail'] = self.detail
        if self.documentation is not None:
            result['documentation'] = self.documentation
        if self.insertText is not None:
            result['insertText'] = self.insertText
        if self.insertTextFormat is not None:
            result['insertTextFormat'] = self.insertTextFormat
        if self.sortText is not None:
            result['sortText'] = self.sortText
        if self.filterText is not None:
            result['filterText'] = self.filterText
        if self.preselect is not None:
            result['preselect'] = self.preselect
        return result


class TextDocumentManager:
    """Manages open text documents"""
    
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
    
    def open(self, item: TextDocumentItem):
        """Open a document"""
        self.documents[item.uri] = {
            'uri': item.uri,
            'languageId': item.languageId,
            'version': item.version,
            'text': item.text,
            'lines': item.text.split('\n')
        }
    
    def close(self, uri: str):
        """Close a document"""
        if uri in self.documents:
            del self.documents[uri]
    
    def change(self, uri: str, version: int, changes: List[TextDocumentContentChangeEvent]):
        """Apply changes to a document"""
        if uri not in self.documents:
            return
        
        doc = self.documents[uri]
        text = doc['text']
        
        for change in changes:
            if change.range is None:
                # Full document change
                text = change.text
            else:
                # Incremental change
                lines = text.split('\n')
                start_line = change.range.start.line
                start_char = change.range.start.character
                end_line = change.range.end.line
                end_char = change.range.end.character
                
                # Apply change
                before = '\n'.join(lines[:start_line]) + ('\n' if start_line > 0 else '') + lines[start_line][:start_char]
                after = lines[end_line][end_char:] + ('\n' if end_line < len(lines) - 1 else '') + '\n'.join(lines[end_line + 1:])
                text = before + change.text + after
        
        doc['text'] = text
        doc['lines'] = text.split('\n')
        doc['version'] = version
    
    def get(self, uri: str) -> Optional[Dict[str, Any]]:
        """Get a document by URI"""
        return self.documents.get(uri)
    
    def get_text(self, uri: str) -> Optional[str]:
        """Get document text"""
        doc = self.documents.get(uri)
        return doc['text'] if doc else None
    
    def get_word_at_position(self, uri: str, position: Position) -> Optional[str]:
        """Get the word at a position"""
        doc = self.documents.get(uri)
        if not doc:
            return None
        
        lines = doc['lines']
        if position.line >= len(lines):
            return None
        
        line = lines[position.line]
        if position.character >= len(line):
            return None
        
        # Find word boundaries
        import re
        word_pattern = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
        
        for match in word_pattern.finditer(line):
            if match.start() <= position.character <= match.end():
                return match.group()
        
        return None


class MrkiLanguageServer:
    """
    Mrki Language Server implementing LSP
    """
    
    # LSP methods
    METHOD_INITIALIZE = 'initialize'
    METHOD_INITIALIZED = 'initialized'
    METHOD_SHUTDOWN = 'shutdown'
    METHOD_EXIT = 'exit'
    
    # Text document methods
    METHOD_TD_OPEN = 'textDocument/didOpen'
    METHOD_TD_CLOSE = 'textDocument/didClose'
    METHOD_TD_CHANGE = 'textDocument/didChange'
    METHOD_TD_SAVE = 'textDocument/didSave'
    
    # Language features
    METHOD_COMPLETION = 'textDocument/completion'
    METHOD_HOVER = 'textDocument/hover'
    METHOD_SIGNATURE_HELP = 'textDocument/signatureHelp'
    METHOD_DEFINITION = 'textDocument/definition'
    METHOD_REFERENCES = 'textDocument/references'
    METHOD_DOCUMENT_SYMBOL = 'textDocument/documentSymbol'
    METHOD_CODE_ACTION = 'textDocument/codeAction'
    METHOD_CODE_LENS = 'textDocument/codeLens'
    METHOD_FORMATTING = 'textDocument/formatting'
    METHOD_RANGE_FORMATTING = 'textDocument/rangeFormatting'
    METHOD_RENAME = 'textDocument/rename'
    
    # Mrki-specific methods
    METHOD_EXPLAIN = 'mrki/explain'
    METHOD_GENERATE_TESTS = 'mrki/generateTests'
    METHOD_REFACTOR = 'mrki/refactor'
    
    def __init__(self, input_stream=None, output_stream=None):
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout
        
        self.documents = TextDocumentManager()
        self.initialized = False
        self.shutdown_received = False
        
        # Server capabilities
        self.capabilities = {
            'textDocumentSync': {
                'openClose': True,
                'change': 2,  # Incremental
                'willSave': False,
                'willSaveWaitUntil': False,
                'save': {'includeText': False}
            },
            'completionProvider': {
                'resolveProvider': False,
                'triggerCharacters': ['.', ':', '>']
            },
            'hoverProvider': True,
            'signatureHelpProvider': {
                'triggerCharacters': ['(', ',']
            },
            'definitionProvider': True,
            'referencesProvider': True,
            'documentSymbolProvider': True,
            'codeActionProvider': True,
            'codeLensProvider': {'resolveProvider': False},
            'documentFormattingProvider': True,
            'documentRangeFormattingProvider': True,
            'documentOnTypeFormattingProvider': {
                'firstTriggerCharacter': ';',
                'moreTriggerCharacter': ['}', ',']
            },
            'renameProvider': True,
            'foldingRangeProvider': True,
            'executeCommandProvider': {
                'commands': ['mrki.explain', 'mrki.generateTests', 'mrki.refactor']
            },
            'selectionRangeProvider': True,
            'semanticTokensProvider': {
                'legend': {
                    'tokenTypes': ['namespace', 'type', 'class', 'enum', 'interface', 'struct', 'typeParameter', 'parameter', 'variable', 'property', 'enumMember', 'event', 'function', 'method', 'macro', 'keyword', 'modifier', 'comment', 'string', 'number', 'regexp', 'operator'],
                    'tokenModifiers': ['declaration', 'definition', 'readonly', 'static', 'deprecated', 'abstract', 'async', 'modification', 'documentation', 'defaultLibrary']
                },
                'full': {'delta': True},
                'range': True
            },
            'inlayHintProvider': True,
            'inlineValueProvider': True,
        }
        
        # Method handlers
        self.handlers: Dict[str, Callable] = {
            self.METHOD_INITIALIZE: self._handle_initialize,
            self.METHOD_INITIALIZED: self._handle_initialized,
            self.METHOD_SHUTDOWN: self._handle_shutdown,
            self.METHOD_EXIT: self._handle_exit,
            self.METHOD_TD_OPEN: self._handle_td_open,
            self.METHOD_TD_CLOSE: self._handle_td_close,
            self.METHOD_TD_CHANGE: self._handle_td_change,
            self.METHOD_TD_SAVE: self._handle_td_save,
            self.METHOD_COMPLETION: self._handle_completion,
            self.METHOD_HOVER: self._handle_hover,
            self.METHOD_DEFINITION: self._handle_definition,
            self.METHOD_REFERENCES: self._handle_references,
            self.METHOD_DOCUMENT_SYMBOL: self._handle_document_symbol,
            self.METHOD_CODE_ACTION: self._handle_code_action,
            self.METHOD_FORMATTING: self._handle_formatting,
            self.METHOD_RENAME: self._handle_rename,
            self.METHOD_EXPLAIN: self._handle_explain,
            self.METHOD_GENERATE_TESTS: self._handle_generate_tests,
            self.METHOD_REFACTOR: self._handle_refactor,
        }
        
        self.logger = logging.getLogger('MrkiLSP')
    
    def log(self, message: str):
        """Log a message"""
        self.logger.info(message)
    
    def send_message(self, message: Dict):
        """Send a message to the client"""
        content = json.dumps(message)
        header = f'Content-Length: {len(content)}\r\n\r\n'
        self.output_stream.write(header + content)
        self.output_stream.flush()
    
    def send_response(self, id: Any, result: Any = None, error: Any = None):
        """Send a response message"""
        message = {'jsonrpc': '2.0', 'id': id}
        if error:
            message['error'] = error
        else:
            message['result'] = result
        self.send_message(message)
    
    def send_notification(self, method: str, params: Any = None):
        """Send a notification message"""
        message = {'jsonrpc': '2.0', 'method': method}
        if params:
            message['params'] = params
        self.send_message(message)
    
    def read_message(self) -> Optional[Dict]:
        """Read a message from the client"""
        # Read headers
        headers = {}
        while True:
            line = self.input_stream.readline()
            if not line:
                return None
            line = line.decode('utf-8') if isinstance(line, bytes) else line
            if line == '\r\n' or line == '\n':
                break
            key, value = line.strip().split(':', 1)
            headers[key.strip()] = value.strip()
        
        # Read content
        content_length = int(headers.get('Content-Length', 0))
        if content_length == 0:
            return None
        
        content = self.input_stream.read(content_length)
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        return json.loads(content)
    
    def run(self):
        """Run the language server"""
        self.log("Mrki Language Server started")
        
        while True:
            try:
                message = self.read_message()
                if message is None:
                    break
                
                self._handle_message(message)
                
                if self.shutdown_received:
                    break
                    
            except Exception as e:
                self.log(f"Error: {e}")
                traceback.print_exc()
    
    def _handle_message(self, message: Dict):
        """Handle an incoming message"""
        method = message.get('method')
        params = message.get('params', {})
        msg_id = message.get('id')
        
        self.log(f"Received: {method}")
        
        if method in self.handlers:
            try:
                result = self.handlers[method](params)
                if msg_id is not None:
                    self.send_response(msg_id, result)
            except Exception as e:
                self.log(f"Error handling {method}: {e}")
                if msg_id is not None:
                    self.send_response(msg_id, error={'code': -32603, 'message': str(e)})
        else:
            self.log(f"Unknown method: {method}")
            if msg_id is not None:
                self.send_response(msg_id, error={'code': -32601, 'message': f'Method not found: {method}'})
    
    # Handler methods
    def _handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request"""
        self.initialized = True
        
        return {
            'capabilities': self.capabilities,
            'serverInfo': {
                'name': 'mrki-lsp',
                'version': '1.0.0'
            }
        }
    
    def _handle_initialized(self, params: Dict) -> None:
        """Handle initialized notification"""
        self.log("Client initialized")
    
    def _handle_shutdown(self, params: Dict) -> None:
        """Handle shutdown request"""
        self.shutdown_received = True
        return None
    
    def _handle_exit(self, params: Dict) -> None:
        """Handle exit notification"""
        sys.exit(0 if self.shutdown_received else 1)
    
    def _handle_td_open(self, params: Dict) -> None:
        """Handle textDocument/didOpen"""
        text_doc = params.get('textDocument', {})
        item = TextDocumentItem(
            uri=text_doc.get('uri', ''),
            languageId=text_doc.get('languageId', ''),
            version=text_doc.get('version', 0),
            text=text_doc.get('text', '')
        )
        self.documents.open(item)
        self.log(f"Opened: {item.uri}")
    
    def _handle_td_close(self, params: Dict) -> None:
        """Handle textDocument/didClose"""
        uri = params.get('textDocument', {}).get('uri', '')
        self.documents.close(uri)
        self.log(f"Closed: {uri}")
    
    def _handle_td_change(self, params: Dict) -> None:
        """Handle textDocument/didChange"""
        uri = params.get('textDocument', {}).get('uri', '')
        version = params.get('textDocument', {}).get('version', 0)
        
        changes = []
        for change in params.get('contentChanges', []):
            if 'range' in change:
                changes.append(TextDocumentContentChangeEvent(
                    range=Range.from_dict(change['range']),
                    rangeLength=change.get('rangeLength'),
                    text=change.get('text', '')
                ))
            else:
                changes.append(TextDocumentContentChangeEvent(
                    range=None,
                    rangeLength=None,
                    text=change.get('text', '')
                ))
        
        self.documents.change(uri, version, changes)
        self.log(f"Changed: {uri}")
    
    def _handle_td_save(self, params: Dict) -> None:
        """Handle textDocument/didSave"""
        uri = params.get('textDocument', {}).get('uri', '')
        self.log(f"Saved: {uri}")
    
    def _handle_completion(self, params: Dict) -> Dict:
        """Handle textDocument/completion"""
        uri = params.get('textDocument', {}).get('uri', '')
        position = Position.from_dict(params.get('position', {}))
        
        # Get document text
        doc_text = self.documents.get_text(uri)
        if not doc_text:
            return {'items': []}
        
        # Get completions from AI backend
        completions = self._get_ai_completions(doc_text, position, uri)
        
        return {'items': [c.to_dict() for c in completions]}
    
    def _get_ai_completions(self, text: str, position: Position, uri: str) -> List[CompletionItem]:
        """Get AI-powered completions"""
        # This would call the actual Mrki AI backend
        # For now, return some example completions
        
        word = self.documents.get_word_at_position(uri, position)
        
        completions = []
        
        if word:
            # Context-aware completions
            if word.startswith('def'):
                completions.append(CompletionItem(
                    label='def function_name():',
                    kind=3,  # Function
                    detail='Function definition',
                    insertText='def ${1:function_name}(${2:args}):\n    ${3:pass}',
                    insertTextFormat=2  # Snippet
                ))
            elif word.startswith('class'):
                completions.append(CompletionItem(
                    label='class ClassName:',
                    kind=7,  # Class
                    detail='Class definition',
                    insertText='class ${1:ClassName}:\n    def __init__(self):\n        ${2:pass}',
                    insertTextFormat=2
                ))
            elif word.startswith('for'):
                completions.append(CompletionItem(
                    label='for item in items:',
                    kind=14,  # Keyword
                    detail='For loop',
                    insertText='for ${1:item} in ${2:items}:\n    ${3:pass}',
                    insertTextFormat=2
                ))
        
        # Add some generic completions
        completions.extend([
            CompletionItem(
                label='if __name__ == "__main__":',
                kind=14,
                insertText='if __name__ == "__main__":\n    ${1:main()}',
                insertTextFormat=2
            ),
            CompletionItem(
                label='try-except',
                kind=14,
                insertText='try:\n    ${1:pass}\nexcept ${2:Exception} as ${3:e}:\n    ${4:pass}',
                insertTextFormat=2
            ),
        ])
        
        return completions
    
    def _handle_hover(self, params: Dict) -> Optional[Dict]:
        """Handle textDocument/hover"""
        uri = params.get('textDocument', {}).get('uri', '')
        position = Position.from_dict(params.get('position', {}))
        
        word = self.documents.get_word_at_position(uri, position)
        if not word:
            return None
        
        # Return hover info
        return {
            'contents': {
                'kind': 'markdown',
                'value': f'**{word}**\n\nSymbol information would appear here.'
            }
        }
    
    def _handle_definition(self, params: Dict) -> List[Dict]:
        """Handle textDocument/definition"""
        # Would return definition locations
        return []
    
    def _handle_references(self, params: Dict) -> List[Dict]:
        """Handle textDocument/references"""
        # Would return reference locations
        return []
    
    def _handle_document_symbol(self, params: Dict) -> List[Dict]:
        """Handle textDocument/documentSymbol"""
        # Would return document symbols
        return []
    
    def _handle_code_action(self, params: Dict) -> List[Dict]:
        """Handle textDocument/codeAction"""
        # Return available code actions
        return [
            {
                'title': 'Explain with Mrki',
                'kind': 'quickfix',
                'command': {
                    'command': 'mrki.explain',
                    'title': 'Explain Code'
                }
            },
            {
                'title': 'Generate tests with Mrki',
                'kind': 'source',
                'command': {
                    'command': 'mrki.generateTests',
                    'title': 'Generate Tests'
                }
            }
        ]
    
    def _handle_formatting(self, params: Dict) -> List[Dict]:
        """Handle textDocument/formatting"""
        # Would return formatting edits
        return []
    
    def _handle_rename(self, params: Dict) -> Optional[Dict]:
        """Handle textDocument/rename"""
        # Would return workspace edit
        return None
    
    def _handle_explain(self, params: Dict) -> str:
        """Handle mrki/explain request"""
        code = params.get('code', '')
        # Would call AI backend for explanation
        return f"This code appears to be a {len(code)} character snippet. AI explanation would go here."
    
    def _handle_generate_tests(self, params: Dict) -> str:
        """Handle mrki/generateTests request"""
        code = params.get('code', '')
        # Would call AI backend to generate tests
        return f"# Generated tests for the provided code\n# (AI-generated tests would appear here)"
    
    def _handle_refactor(self, params: Dict) -> str:
        """Handle mrki/refactor request"""
        code = params.get('code', '')
        # Would call AI backend to refactor
        return code  # Return original for now


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Mrki Language Server')
    parser.add_argument('--port', type=int, default=8765, help='Server port')
    parser.add_argument('--stdio', action='store_true', help='Use stdio for communication')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            filename='/tmp/mrki-lsp.log',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    server = MrkiLanguageServer()
    server.run()


if __name__ == '__main__':
    main()
