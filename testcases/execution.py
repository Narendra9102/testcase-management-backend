"""
Test Case Execution Engine
Supports both simulation and AI-driven execution (OpenAI/Anthropic)
"""
import time
import random
import json
from datetime import datetime


class TestExecutionEngine:
    """
    Handles test case execution with two modes:
    1. Simulation mode (no AI required)
    2. AI-driven mode (OpenAI or Anthropic)
    """
    
    def __init__(self, testcase, executed_by, ai_config=None):
        """
        Args:
            testcase: TestCase model instance
            executed_by: User who triggered execution
            ai_config: Optional dict with 'provider', 'api_key', 'model'
        """
        self.testcase = testcase
        self.executed_by = executed_by
        self.ai_config = ai_config
        self.execution_log = []
    
    def execute(self):
        """
        Main execution method
        Returns: dict with status, execution_time, error_message, log
        """
        start_time = time.time()
        
        try:
            # Check if AI execution is requested
            if self.ai_config and self.ai_config.get('api_key'):
                result = self._execute_with_ai()
            else:
                result = self._execute_simulation()
            
            execution_time = time.time() - start_time
            
            return {
                'status': result['status'],
                'execution_time': round(execution_time, 2),
                'error_message': result.get('error_message'),
                'execution_log': self.execution_log,
                'ai_used': bool(self.ai_config and self.ai_config.get('api_key'))
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'status': 'Failed',
                'execution_time': round(execution_time, 2),
                'error_message': f"Execution error: {str(e)}",
                'execution_log': self.execution_log,
                'ai_used': False
            }
    
    def _execute_simulation(self):
        """
        Simulates test execution without AI
        80% pass rate, 20% fail rate
        """
        self.execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'message': 'Starting simulated execution...',
            'type': 'info'
        })
        
        # Parse test steps
        steps = self._parse_steps(self.testcase.steps)
        
        self.execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'message': f'Found {len(steps)} steps to execute',
            'type': 'info'
        })
        
        # Simulate each step execution
        for i, step in enumerate(steps, 1):
            time.sleep(0.3)  # Simulate processing time
            
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'message': f'Step {i}: {step[:60]}...',
                'type': 'step'
            })
        
        # Simulate result (80% pass, 20% fail)
        passed = random.random() < 0.8
        
        if passed:
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'message': 'All steps executed successfully',
                'type': 'success'
            })
            return {'status': 'Passed', 'error_message': None}
        else:
            failed_step = random.randint(1, len(steps))
            error_msg = f"Step {failed_step} failed: Element not found or assertion failed"
            
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'message': error_msg,
                'type': 'error'
            })
            return {'status': 'Failed', 'error_message': error_msg}
    
    def _execute_with_ai(self):
        """
        AI-driven execution using OpenAI or Anthropic
        Validates test steps and provides intelligent feedback
        """
        provider = self.ai_config.get('provider', 'openai').lower()
        api_key = self.ai_config['api_key']
        model = self.ai_config.get('model', 'gpt-4o-mini' if provider == 'openai' else 'claude-sonnet-4-20250514')
        
        self.execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'message': f'Starting AI-driven execution with {provider}...',
            'type': 'info'
        })
        
        try:
            if provider == 'openai':
                return self._execute_with_openai(api_key, model)
            elif provider == 'anthropic':
                return self._execute_with_anthropic(api_key, model)
            else:
                raise ValueError(f"Unsupported AI provider: {provider}")
                
        except Exception as e:
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'message': f'AI execution failed: {str(e)}. Falling back to simulation.',
                'type': 'warning'
            })
            return self._execute_simulation()
    
    def _execute_with_openai(self, api_key, model):
        """Execute using OpenAI API"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        client = OpenAI(api_key=api_key)
        
        # Prepare prompt for AI validation
        prompt = self._build_ai_prompt()
        
        self.execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'message': f'Sending test case to OpenAI ({model})...',
            'type': 'info'
        })
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test execution validator. Analyze test cases and provide validation results in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'message': 'Received AI validation response',
                'type': 'info'
            })
            
            # Parse AI response
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _execute_with_anthropic(self, api_key, model):
        """Execute using Anthropic API"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = self._build_ai_prompt()
        
        self.execution_log.append({
            'timestamp': datetime.now().isoformat(),
            'message': f'Sending test case to Anthropic ({model})...',
            'type': 'info'
        })
        
        try:
            response = client.messages.create(
                model=model,
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            ai_response = response.content[0].text
            
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'message': 'Received AI validation response',
                'type': 'info'
            })
            
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _build_ai_prompt(self):
        """Build prompt for AI validation"""
        return f"""Analyze this test case and validate if it's executable:

**Test Case Details:**
- Title: {self.testcase.title}
- Description: {self.testcase.description}
- Steps: {self.testcase.steps}
- Expected Result: {self.testcase.expected_result}
- Priority: {self.testcase.priority}

**Your Task:**
1. Validate if the test steps are clear and executable
2. Check if expected result is realistic
3. Identify any potential issues or missing information
4. Provide a validation result

**Response Format (JSON only):**
{{
    "status": "Passed" or "Failed",
    "confidence": 0.0-1.0,
    "issues": ["list of issues found"],
    "recommendations": ["suggestions for improvement"],
    "error_message": "explanation if failed, null if passed"
}}

Respond ONLY with valid JSON, no other text."""
    
    def _parse_ai_response(self, ai_response):
        """Parse AI validation response"""
        try:
            # Try to extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                result = json.loads(json_str)
                
                # Log AI findings
                if result.get('issues'):
                    for issue in result['issues']:
                        self.execution_log.append({
                            'timestamp': datetime.now().isoformat(),
                            'message': f'AI detected issue: {issue}',
                            'type': 'warning'
                        })
                
                if result.get('recommendations'):
                    for rec in result['recommendations']:
                        self.execution_log.append({
                            'timestamp': datetime.now().isoformat(),
                            'message': f'AI recommendation: {rec}',
                            'type': 'info'
                        })
                
                status = result.get('status', 'Failed')
                confidence = result.get('confidence', 0.0)
                
                self.execution_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f'AI validation result: {status} (confidence: {confidence:.2f})',
                    'type': 'success' if status == 'Passed' else 'error'
                })
                
                return {
                    'status': status,
                    'error_message': result.get('error_message')
                }
            else:
                raise ValueError("No valid JSON found in AI response")
                
        except Exception as e:
            self.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'message': f'Failed to parse AI response: {str(e)}',
                'type': 'error'
            })
            # Fallback to simulation
            return self._execute_simulation()
    
    def _parse_steps(self, steps_text):
        """Parse test steps from text"""
        if not steps_text:
            return []
        
        # Split by common delimiters
        lines = steps_text.replace('\r\n', '\n').split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            # Remove numbering (1., 2., Step 1:, etc.)
            line = line.lstrip('0123456789.-) ').lstrip('Step :')
            if line:
                steps.append(line)
        
        return steps if steps else [steps_text]
    