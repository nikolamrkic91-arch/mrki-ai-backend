#!/usr/bin/env python3
"""
Mrki Debug Adapter Protocol (DAP) Implementation
"""

import argparse
import json
import logging
import sys
import threading
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union


class StoppedReason(Enum):
    """Reason why execution stopped"""
    STEP = 'step'
    BREAKPOINT = 'breakpoint'
    EXCEPTION = 'exception'
    PAUSE = 'pause'
    ENTRY = 'entry'
    GOTO = 'goto'
    FUNCTION_BREAKPOINT = 'function breakpoint'
    DATA_BREAKPOINT = 'data breakpoint'
    INSTRUCTION_BREAKPOINT = 'instruction breakpoint'


@dataclass
class StackFrame:
    """Stack frame information"""
    id: int
    name: str
    source: Optional[Dict]
    line: int
    column: int
    
    def to_dict(self) -> Dict:
        result = {
            'id': self.id,
            'name': self.name,
            'line': self.line,
            'column': self.column
        }
        if self.source:
            result['source'] = self.source
        return result


@dataclass
class Breakpoint:
    """Breakpoint information"""
    id: Optional[int]
    verified: bool
    line: Optional[int]
    message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {'verified': self.verified}
        if self.id is not None:
            result['id'] = self.id
        if self.line is not None:
            result['line'] = self.line
        if self.message is not None:
            result['message'] = self.message
        return result


@dataclass
class Thread:
    """Thread information"""
    id: int
    name: str
    
    def to_dict(self) -> Dict:
        return {'id': self.id, 'name': self.name}


@dataclass
class Variable:
    """Variable information"""
    name: str
    value: str
    type: Optional[str] = None
    variablesReference: int = 0
    
    def to_dict(self) -> Dict:
        result = {
            'name': self.name,
            'value': self.value,
            'variablesReference': self.variablesReference
        }
        if self.type:
            result['type'] = self.type
        return result


class DebugSession:
    """Debug session state"""
    
    def __init__(self):
        self.initialized = False
        self.configuration_done = False
        self.threads: Dict[int, Thread] = {}
        self.breakpoints: Dict[str, List[Breakpoint]] = {}
        self.stack_frames: Dict[int, StackFrame] = {}
        self.variables: Dict[int, List[Variable]] = {}
        self.next_frame_id = 1
        self.next_var_ref = 1
        self.current_thread_id: Optional[int] = None
        self.running = False
        self.program: Optional[str] = None
        self.args: List[str] = []
        self.env: Dict[str, str] = {}
        self.cwd: Optional[str] = None


class MrkiDebugAdapter:
    """
    Mrki Debug Adapter implementing DAP
    """
    
    # DAP methods
    METHOD_INITIALIZE = 'initialize'
    METHOD_CONFIGURATION_DONE = 'configurationDone'
    METHOD_LAUNCH = 'launch'
    METHOD_ATTACH = 'attach'
    METHOD_DISCONNECT = 'disconnect'
    METHOD_TERMINATE = 'terminate'
    
    # Thread control
    METHOD_CONTINUE = 'continue'
    METHOD_NEXT = 'next'
    METHOD_STEP_IN = 'stepIn'
    METHOD_STEP_OUT = 'stepOut'
    METHOD_PAUSE = 'pause'
    
    # Stack and variables
    METHOD_STACK_TRACE = 'stackTrace'
    METHOD_SCOPES = 'scopes'
    METHOD_VARIABLES = 'variables'
    
    # Breakpoints
    METHOD_SET_BREAKPOINTS = 'setBreakpoints'
    METHOD_SET_FUNCTION_BREAKPOINTS = 'setFunctionBreakpoints'
    METHOD_SET_EXCEPTION_BREAKPOINTS = 'setExceptionBreakpoints'
    
    # Evaluation
    METHOD_EVALUATE = 'evaluate'
    METHOD_SOURCE = 'source'
    METHOD_THREADS = 'threads'
    
    def __init__(self, input_stream=None, output_stream=None):
        self.input_stream = input_stream or sys.stdin.buffer
        self.output_stream = output_stream or sys.stdout.buffer
        
        self.session = DebugSession()
        self.seq = 0
        
        # Capabilities
        self.capabilities = {
            'supportsConfigurationDoneRequest': True,
            'supportsFunctionBreakpoints': True,
            'supportsConditionalBreakpoints': True,
            'supportsHitConditionalBreakpoints': True,
            'supportsEvaluateForHovers': True,
            'exceptionBreakpointFilters': [
                {
                    'filter': 'raised',
                    'label': 'Raised Exceptions',
                    'default': True
                },
                {
                    'filter': 'uncaught',
                    'label': 'Uncaught Exceptions',
                    'default': True
                }
            ],
            'supportsStepBack': False,
            'supportsSetVariable': True,
            'supportsRestartFrame': False,
            'supportsGotoTargetsRequest': False,
            'supportsStepInTargetsRequest': False,
            'supportsCompletionsRequest': True,
            'supportsModulesRequest': False,
            'additionalModuleColumns': [],
            'supportedChecksumAlgorithms': [],
            'supportsRestartRequest': True,
            'supportsExceptionOptions': True,
            'supportsValueFormattingOptions': True,
            'supportsExceptionInfoRequest': True,
            'supportTerminateDebuggee': True,
            'supportsDelayedStackTraceLoading': True,
            'supportsLoadedSourcesRequest': False,
            'supportsLogPoints': True,
            'supportsTerminateThreadsRequest': False,
            'supportsSetExpression': False,
            'supportsTerminateRequest': True,
            'supportsDataBreakpoints': False,
            'supportsReadMemoryRequest': False,
            'supportsWriteMemoryRequest': False,
            'supportsDisassembleRequest': False,
            'supportsCancelRequest': False,
            'supportsBreakpointLocationsRequest': True,
            'supportsClipboardContext': True,
            'supportsSteppingGranularity': False,
            'supportsInstructionBreakpoints': False
        }
        
        # Method handlers
        self.handlers: Dict[str, Callable] = {
            self.METHOD_INITIALIZE: self._handle_initialize,
            self.METHOD_CONFIGURATION_DONE: self._handle_configuration_done,
            self.METHOD_LAUNCH: self._handle_launch,
            self.METHOD_ATTACH: self._handle_attach,
            self.METHOD_DISCONNECT: self._handle_disconnect,
            self.METHOD_TERMINATE: self._handle_terminate,
            self.METHOD_CONTINUE: self._handle_continue,
            self.METHOD_NEXT: self._handle_next,
            self.METHOD_STEP_IN: self._handle_step_in,
            self.METHOD_STEP_OUT: self._handle_step_out,
            self.METHOD_PAUSE: self._handle_pause,
            self.METHOD_STACK_TRACE: self._handle_stack_trace,
            self.METHOD_SCOPES: self._handle_scopes,
            self.METHOD_VARIABLES: self._handle_variables,
            self.METHOD_SET_BREAKPOINTS: self._handle_set_breakpoints,
            self.METHOD_SET_FUNCTION_BREAKPOINTS: self._handle_set_function_breakpoints,
            self.METHOD_SET_EXCEPTION_BREAKPOINTS: self._handle_set_exception_breakpoints,
            self.METHOD_EVALUATE: self._handle_evaluate,
            self.METHOD_SOURCE: self._handle_source,
            self.METHOD_THREADS: self._handle_threads,
        }
        
        self.logger = logging.getLogger('MrkiDAP')
    
    def log(self, message: str):
        """Log a message"""
        self.logger.info(message)
    
    def send_message(self, message: Dict):
        """Send a message to the client"""
        content = json.dumps(message).encode('utf-8')
        header = f'Content-Length: {len(content)}\r\n\r\n'.encode('utf-8')
        self.output_stream.write(header + content)
        self.output_stream.flush()
    
    def send_response(self, request_seq: int, command: str, 
                     result: Any = None, error: Any = None):
        """Send a response message"""
        self.seq += 1
        message = {
            'seq': self.seq,
            'type': 'response',
            'request_seq': request_seq,
            'success': error is None,
            'command': command
        }
        if error:
            message['message'] = error
        else:
            message['body'] = result
        self.send_message(message)
    
    def send_event(self, event: str, body: Any = None):
        """Send an event message"""
        self.seq += 1
        message = {
            'seq': self.seq,
            'type': 'event',
            'event': event
        }
        if body:
            message['body'] = body
        self.send_message(message)
    
    def read_message(self) -> Optional[Dict]:
        """Read a message from the client"""
        # Read headers
        headers = {}
        while True:
            try:
                line = self.input_stream.readline()
                if not line:
                    return None
                line = line.decode('utf-8')
                if line == '\r\n' or line == '\n':
                    break
                if ':' in line:
                    key, value = line.strip().split(':', 1)
                    headers[key.strip()] = value.strip()
            except Exception as e:
                self.log(f"Error reading header: {e}")
                return None
        
        # Read content
        content_length = int(headers.get('Content-Length', 0))
        if content_length == 0:
            return None
        
        content = self.input_stream.read(content_length)
        content = content.decode('utf-8')
        
        return json.loads(content)
    
    def run(self):
        """Run the debug adapter"""
        self.log("Mrki Debug Adapter started")
        
        while True:
            try:
                message = self.read_message()
                if message is None:
                    break
                
                self._handle_message(message)
                
            except Exception as e:
                self.log(f"Error: {e}")
                traceback.print_exc()
    
    def _handle_message(self, message: Dict):
        """Handle an incoming message"""
        msg_type = message.get('type')
        command = message.get('command')
        msg_seq = message.get('seq', 0)
        
        if msg_type != 'request':
            return
        
        self.log(f"Received: {command}")
        
        if command in self.handlers:
            try:
                result = self.handlers[command](message.get('arguments', {}))
                self.send_response(msg_seq, command, result)
            except Exception as e:
                self.log(f"Error handling {command}: {e}")
                self.send_response(msg_seq, command, error=str(e))
        else:
            self.log(f"Unknown command: {command}")
            self.send_response(msg_seq, command, error=f'Unknown command: {command}')
    
    # Handler methods
    def _handle_initialize(self, args: Dict) -> Dict:
        """Handle initialize request"""
        self.session.initialized = True
        
        # Send initialized event
        self.send_event('initialized')
        
        return self.capabilities
    
    def _handle_configuration_done(self, args: Dict) -> None:
        """Handle configurationDone request"""
        self.session.configuration_done = True
        
        # Start debugging if launch was already received
        if self.session.program and not self.session.running:
            self._start_debugging()
    
    def _handle_launch(self, args: Dict) -> None:
        """Handle launch request"""
        self.session.program = args.get('program')
        self.session.args = args.get('args', [])
        self.session.env = args.get('env', {})
        self.session.cwd = args.get('cwd')
        
        self.log(f"Launch: {self.session.program}")
        
        # Start debugging if configuration is done
        if self.session.configuration_done:
            self._start_debugging()
    
    def _handle_attach(self, args: Dict) -> None:
        """Handle attach request"""
        self.log("Attach not implemented")
        raise NotImplementedError("Attach not implemented")
    
    def _handle_disconnect(self, args: Dict) -> None:
        """Handle disconnect request"""
        self.log("Disconnect")
        self._stop_debugging()
    
    def _handle_terminate(self, args: Dict) -> None:
        """Handle terminate request"""
        self.log("Terminate")
        self._stop_debugging()
    
    def _handle_continue(self, args: Dict) -> Dict:
        """Handle continue request"""
        thread_id = args.get('threadId')
        self.log(f"Continue thread {thread_id}")
        
        self.session.running = True
        
        # Simulate execution
        threading.Timer(2.0, self._simulate_stop).start()
        
        return {'allThreadsContinued': True}
    
    def _handle_next(self, args: Dict) -> None:
        """Handle next (step over) request"""
        thread_id = args.get('threadId')
        self.log(f"Next thread {thread_id}")
        
        # Simulate step
        threading.Timer(0.5, lambda: self._simulate_stop(StoppedReason.STEP)).start()
    
    def _handle_step_in(self, args: Dict) -> None:
        """Handle stepIn request"""
        thread_id = args.get('threadId')
        self.log(f"StepIn thread {thread_id}")
        
        threading.Timer(0.5, lambda: self._simulate_stop(StoppedReason.STEP)).start()
    
    def _handle_step_out(self, args: Dict) -> None:
        """Handle stepOut request"""
        thread_id = args.get('threadId')
        self.log(f"StepOut thread {thread_id}")
        
        threading.Timer(0.5, lambda: self._simulate_stop(StoppedReason.STEP)).start()
    
    def _handle_pause(self, args: Dict) -> None:
        """Handle pause request"""
        thread_id = args.get('threadId')
        self.log(f"Pause thread {thread_id}")
        
        self._simulate_stop(StoppedReason.PAUSE)
    
    def _handle_stack_trace(self, args: Dict) -> Dict:
        """Handle stackTrace request"""
        thread_id = args.get('threadId')
        start_frame = args.get('startFrame', 0)
        levels = args.get('levels', 20)
        
        self.log(f"Stack trace for thread {thread_id}")
        
        # Return mock stack frames
        frames = []
        for i in range(min(levels, 5)):
            frame_id = self.session.next_frame_id
            self.session.next_frame_id += 1
            
            frame = StackFrame(
                id=frame_id,
                name=f'frame_{i}',
                source={
                    'name': Path(self.session.program).name if self.session.program else 'main.py',
                    'path': self.session.program or 'main.py'
                },
                line=10 + i,
                column=0
            )
            frames.append(frame)
            self.session.stack_frames[frame_id] = frame
        
        return {
            'stackFrames': [f.to_dict() for f in frames],
            'totalFrames': len(frames)
        }
    
    def _handle_scopes(self, args: Dict) -> Dict:
        """Handle scopes request"""
        frame_id = args.get('frameId')
        self.log(f"Scopes for frame {frame_id}")
        
        # Return mock scopes
        var_ref = self.session.next_var_ref
        self.session.next_var_ref += 1
        
        return {
            'scopes': [
                {
                    'name': 'Locals',
                    'variablesReference': var_ref,
                    'expensive': False
                },
                {
                    'name': 'Globals',
                    'variablesReference': var_ref + 1,
                    'expensive': False
                }
            ]
        }
    
    def _handle_variables(self, args: Dict) -> Dict:
        """Handle variables request"""
        var_ref = args.get('variablesReference')
        self.log(f"Variables for ref {var_ref}")
        
        # Return mock variables
        variables = [
            Variable(name='x', value='10', type='int'),
            Variable(name='y', value='"hello"', type='str'),
            Variable(name='data', value='[1, 2, 3]', type='list'),
        ]
        
        return {
            'variables': [v.to_dict() for v in variables]
        }
    
    def _handle_set_breakpoints(self, args: Dict) -> Dict:
        """Handle setBreakpoints request"""
        source = args.get('source', {})
        breakpoints = args.get('breakpoints', [])
        
        source_path = source.get('path', '')
        self.log(f"Set breakpoints for {source_path}: {len(breakpoints)} breakpoints")
        
        # Store breakpoints
        self.session.breakpoints[source_path] = []
        result = []
        
        for i, bp in enumerate(breakpoints):
            breakpoint = Breakpoint(
                id=i + 1,
                verified=True,
                line=bp.get('line')
            )
            self.session.breakpoints[source_path].append(breakpoint)
            result.append(breakpoint.to_dict())
        
        return {'breakpoints': result}
    
    def _handle_set_function_breakpoints(self, args: Dict) -> Dict:
        """Handle setFunctionBreakpoints request"""
        breakpoints = args.get('breakpoints', [])
        self.log(f"Set function breakpoints: {len(breakpoints)}")
        
        return {'breakpoints': []}
    
    def _handle_set_exception_breakpoints(self, args: Dict) -> None:
        """Handle setExceptionBreakpoints request"""
        filters = args.get('filters', [])
        self.log(f"Set exception breakpoints: {filters}")
    
    def _handle_evaluate(self, args: Dict) -> Dict:
        """Handle evaluate request"""
        expression = args.get('expression', '')
        self.log(f"Evaluate: {expression}")
        
        # Mock evaluation
        return {
            'result': f'Result of: {expression}',
            'type': 'str',
            'variablesReference': 0
        }
    
    def _handle_source(self, args: Dict) -> Dict:
        """Handle source request"""
        source = args.get('source', {})
        source_path = source.get('path', '')
        self.log(f"Source: {source_path}")
        
        # Return mock source
        try:
            if source_path and Path(source_path).exists():
                content = Path(source_path).read_text()
            else:
                content = '# Source not available'
        except:
            content = '# Error reading source'
        
        return {'content': content}
    
    def _handle_threads(self, args: Dict) -> Dict:
        """Handle threads request"""
        self.log("Threads")
        
        # Return mock threads
        threads = [
            Thread(id=1, name='MainThread')
        ]
        
        return {
            'threads': [t.to_dict() for t in threads]
        }
    
    def _start_debugging(self):
        """Start debugging session"""
        self.log("Starting debugging session")
        
        # Create main thread
        self.session.threads[1] = Thread(id=1, name='MainThread')
        self.session.current_thread_id = 1
        
        # Send thread started event
        self.send_event('thread', {'reason': 'started', 'threadId': 1})
        
        # Simulate entry stop
        self._simulate_stop(StoppedReason.ENTRY)
    
    def _stop_debugging(self):
        """Stop debugging session"""
        self.log("Stopping debugging session")
        
        self.session.running = False
        
        # Send terminated event
        self.send_event('terminated', {})
        self.send_event('exited', {'exitCode': 0})
    
    def _simulate_stop(self, reason: StoppedReason = StoppedReason.BREAKPOINT):
        """Simulate a stop event"""
        if not self.session.running:
            return
        
        self.session.running = False
        
        self.send_event('stopped', {
            'reason': reason.value,
            'threadId': self.session.current_thread_id,
            'allThreadsStopped': True
        })


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Mrki Debug Adapter')
    parser.add_argument('--port', type=int, default=8766, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            filename='/tmp/mrki-dap.log',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    adapter = MrkiDebugAdapter()
    adapter.run()


if __name__ == '__main__':
    main()
