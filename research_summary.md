# Research Summary: Secure Python Code Execution Libraries

## Overview

This document evaluates secure alternatives to the current `exec()` implementation in the `InterpreterExecutor`. The current implementation has critical security vulnerabilities that allow arbitrary code execution despite basic sanitization attempts.

## Security Requirements

Based on the security analysis, the replacement solution must address:
- Prevent arbitrary system access
- Limit available built-ins and modules safely
- Enforce resource limits (CPU, memory, execution time)
- Provide safe execution environment without compromising functionality

## Evaluated Alternatives

### 1. RestrictedPython

**Description:** A library designed specifically to provide a sandboxed environment for executing Python code. It uses Abstract Syntax Tree (AST) manipulation to restrict what operations are allowed.

**Pros:**
- Purpose-built for secure Python code execution
- Fine-grained control over available operations and objects
- Can define custom policies for allowed operations
- Prevents access to dangerous built-ins by design
- Well-maintained with active community

**Cons:**
- Learning curve for defining security policies
- May require significant refactoring to adapt existing code
- Some legitimate operations may need to be explicitly allowed

**Implementation Complexity:** Medium to High
**Security Level:** High
**Performance Impact:** Moderate

### 2. AST-Based Validation (ast.literal_eval + Custom Node Visitor)

**Description:** Using Python's `ast` module to parse code and validate nodes before execution, combined with a custom node visitor to ensure only safe operations are allowed.

**Pros:**
- Native Python module (part of standard library)
- Fine-grained control over what operations are allowed
- Can be tailored specifically for our use case
- No external dependencies required

**Cons:**
- Complex to implement correctly
- Easy to miss edge cases that could introduce vulnerabilities
- Requires deep understanding of Python AST
- Maintenance overhead for keeping up with Python language changes

**Implementation Complexity:** High
**Security Level:** Variable (depends on implementation quality)
**Performance Impact:** Low to Moderate

### 3. Pyodide

**Description:** Runs Python in the browser using WebAssembly. Can be used in server-side contexts for isolated Python execution.

**Pros:**
- Runs in completely isolated environment
- Well-tested security model
- Full Python ecosystem accessible
- Sandboxed by design

**Cons:**
- Adds significant overhead for simple operations
- More complex deployment/setup
- Primarily designed for browser environments
- Larger resource footprint

**Implementation Complexity:** Medium
**Security Level:** Very High
**Performance Impact:** High

### 4. subprocess + Container Isolation

**Description:** Execute Python code in an isolated subprocess or container with limited resources and access.

**Pros:**
- Strong isolation between execution and host
- Can enforce hard resource limits
- Process can be terminated easily
- Completely prevents system access

**Cons:**
- Higher latency for execution
- More complex setup and orchestration
- Additional infrastructure requirements

**Implementation Complexity:** Medium to High
**Security Level:** Very High
**Performance Impact:** High

### 5. Simple ast.literal_eval for Expression Evaluation

**Description:** Limited to evaluating only literal expressions (strings, numbers, tuples, lists, dicts, booleans, and None).

**Pros:**
- Very secure (only handles literals)
- Part of standard library
- Minimal overhead

**Cons:**
- Extremely limited functionality (cannot execute functions, variables, etc.)
- Would require redesigning how the interpreter works
- Not suitable for complex Python code execution

**Implementation Complexity:** Low
**Security Level:** Very High (but very limited)
**Performance Impact:** Low

## Recommendation

**Primary Recommendation: RestrictedPython**

RestrictedPython is the most suitable solution because:
1. It is specifically designed for this use case
2. Provides strong security guarantees by default
3. Offers granular control over allowed operations
4. Maintains good compatibility with legitimate Python code
5. Has established security practices and active maintenance

**Alternative Recommendation: AST-based validation with extensive testing**

If we need maximum control and can invest in proper security review, a custom AST-based solution could be viable. However, this would require:
- Extensive security auditing
- Continuous maintenance to address new Python features and potential bypasses
- Comprehensive test suite for security edge cases

## Implementation Path Forward

### With RestrictedPython:
1. Install the RestrictedPython package
2. Replace current `exec()` call with RestrictedPython execution
3. Define a security policy that allows the required modules and functions
4. Add resource limits (timeouts, memory)
5. Update tests to verify security

### Security Policy Considerations:
- Allow only safe built-ins like `range`, `len`, `str`, `int`, etc.
- Carefully control access to imported modules
- Implement execution timeouts
- Sanitize error output to prevent information disclosure

## Conclusion

RestrictedPython offers the best balance of security, functionality, and implementation complexity for this use case. It addresses the core vulnerabilities of the current implementation while maintaining reasonable compatibility with existing code patterns.

The security analysis indicates that ad-hoc sanitization approaches (like the current one) are insufficient. Using a purpose-built solution like RestrictedPython is a significantly safer approach than trying to manually sanitize the execution environment.