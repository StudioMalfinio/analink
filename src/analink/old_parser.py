from analink.old_models import InkScript, Choice, Knot, Stitch, VariableChange, WeaveElement
import re

class InkParser():
    """Parser for Ink script files"""
    
    @staticmethod
    def parse_file(filepath: str) -> InkScript:
        """Parse an Ink file and return an InkScript object."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{filepath}' not found.")
        except UnicodeDecodeError:
            raise UnicodeDecodeError(f"Could not decode file '{filepath}'. Check encoding.")
            
        return InkParser.parse_content(content)
    
    @staticmethod
    def _count_leading_chars(line: str, char: str) -> int:
        """Count leading characters (for nesting level)"""
        count = 0
        for c in line:
            if c == char:
                count += 1
            elif c == ' ' or c == '\t':
                continue
            else:
                break
        return count
    
    @staticmethod
    def _get_nesting_level(line: str) -> int:
        """Get the nesting level based on leading tabs/spaces"""
        tabs = InkParser._count_leading_chars(line, '\t')
        if tabs > 0:
            return tabs
        # Convert spaces to approximate tab level (assuming 4 spaces = 1 tab)
        spaces = InkParser._count_leading_chars(line, ' ')
        return spaces // 4
    
    @staticmethod
    def parse_content(content: str) -> InkScript:
        """Parse Ink content and extract knots, stitches, choices, weave, and paths."""
        lines = content.split('\n')
        ink_script = InkScript()
        
        current_knot = None
        current_stitch = None
        current_content = []
        line_number = 0
        weave_stack = []  # Stack to track weave nesting
        
        for i, line in enumerate(lines):
            line_number = i + 1
            original_line = line
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('//'):
                continue
                
            # Handle includes
            if stripped.startswith('INCLUDE'):
                include_file = stripped.split()[1]
                ink_script.includes.append(include_file)
                continue
                
            # Handle variable declarations
            if stripped.startswith('VAR '):
                var_match = re.match(r'VAR\s+(\w+)\s*=\s*(.+)', stripped)
                if var_match:
                    var_name, var_value = var_match.groups()
                    # Try to parse the value
                    try:
                        if var_value.lower() == 'true':
                            ink_script.variables[var_name] = True
                        elif var_value.lower() == 'false':
                            ink_script.variables[var_name] = False
                        elif var_value.isdigit():
                            ink_script.variables[var_name] = int(var_value)
                        elif var_value.startswith('"') and var_value.endswith('"'):
                            ink_script.variables[var_name] = var_value[1:-1]
                        else:
                            ink_script.variables[var_name] = var_value
                    except:
                        ink_script.variables[var_name] = var_value
                continue
            
            # Handle knot definitions (=== knot_name ===)
            if re.match(r'^={2,}\s+.*\s+={2,}$', stripped):
                # Save previous content
                InkParser._save_current_content(current_knot, current_stitch, current_content, ink_script)
                
                # Start new knot
                knot_name = re.sub(r'^={2,}\s*(.*?)\s*={2,}$', r'\1', stripped).strip()
                current_knot = Knot(
                    name=knot_name,
                    line_number=line_number
                )
                current_stitch = None
                current_content = []
                weave_stack = []
                continue
            
            # Handle stitch definitions (= stitch_name)
            if stripped.startswith('=') and not stripped.startswith('=='):
                # Save previous stitch if exists
                if current_stitch:
                    current_stitch.content = '\n'.join(current_content)
                    if current_knot:
                        current_knot.stitches[current_stitch.name] = current_stitch
                
                # Start new stitch
                stitch_name = stripped.lstrip('=').strip()
                current_stitch = Stitch(
                    name=stitch_name,
                    line_number=line_number
                )
                current_content = []
                weave_stack = []
                continue
            
            # If we're in a knot or stitch, process content
            if current_knot:
                target_container = current_stitch if current_stitch else current_knot
                nesting_level = InkParser._get_nesting_level(original_line)
                
                # Handle variable assignments like ~ var = value or ~ var += item
                if stripped.startswith('~'):
                    var_assignment = stripped[1:].strip()
                    target_container.variable_changes.append(
                        VariableChange(change_type='assignment', expression=var_assignment)
                    )
                    continue
                
                # Handle gather points (-)
                if re.match(r'^-+\s', stripped):
                    gather_content = re.sub(r'^-+\s*', '', stripped)
                    weave_element = WeaveElement(
                        type='gather',
                        content=gather_content,
                        nesting_level=nesting_level,
                        line_number=line_number
                    )
                    target_container.weave_elements.append(weave_element)
                    continue
                
                # Handle choices (both * and +)
                choice_match = re.match(r'([*+])\s*(\{[^}]*\})?\s*\[([^\]]*)\](.*)$', stripped)
                if choice_match:
                    choice_type, condition, choice_text, remainder = choice_match.groups()
                    
                    # Check if there's a direct target (-> target)
                    target = None
                    choice_content = remainder.strip()
                    target_match = re.match(r'\s*->\s*(\w+(?:\.\w+)?)', choice_content)
                    if target_match:
                        target = target_match.group(1)
                        choice_content = re.sub(r'\s*->\s*\w+(?:\.\w+)?', '', choice_content)
                    
                    if condition:
                        condition = condition.strip('{}').strip()
                    
                    choice = Choice(
                        text=choice_text,
                        target=target,
                        condition=condition,
                        line_number=line_number,
                        sticky=(choice_type == '+'),
                        content=choice_content,
                        nesting_level=nesting_level
                    )
                    
                    # Create weave element for this choice
                    weave_element = WeaveElement(
                        type='choice',
                        content=choice_content,
                        choices=[choice],
                        nesting_level=nesting_level,
                        line_number=line_number
                    )
                    target_container.weave_elements.append(weave_element)
                    
                    # Also add to choices list for backward compatibility
                    target_container.choices.append(choice)
                    continue
                
                # Handle direct redirects
                redirect_match = re.match(r'->\s*(\w+(?:\.\w+)?)', stripped)
                if redirect_match:
                    target = redirect_match.group(1)
                    if not target_container.fallback_target:
                        target_container.fallback_target = target
                    continue
                
                # Regular content - add as weave element if we have weave structure
                if target_container.weave_elements or nesting_level > 0:
                    weave_element = WeaveElement(
                        type='content',
                        content=original_line,
                        nesting_level=nesting_level,
                        line_number=line_number
                    )
                    target_container.weave_elements.append(weave_element)
                else:
                    # Regular content
                    current_content.append(original_line)
        
        # Save the final content
        InkParser._save_current_content(current_knot, current_stitch, current_content, ink_script)
            
        return ink_script
    
    @staticmethod
    def _save_current_content(current_knot, current_stitch, current_content, ink_script):
        """Helper method to save current content state"""
        # Save stitch if exists
        if current_stitch:
            if not current_stitch.weave_elements:  # Only set content if no weave
                current_stitch.content = '\n'.join(current_content)
            if current_knot:
                current_knot.stitches[current_stitch.name] = current_stitch
        
        # Save knot if exists
        if current_knot:
            # If we were working on a knot directly (no stitches), save its content
            if not current_knot.stitches and not current_knot.weave_elements:
                current_knot.content = '\n'.join(current_content)
            ink_script.knots[current_knot.name] = current_knot