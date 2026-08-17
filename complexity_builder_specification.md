# Complexity Builder

## Overview

The goal of **Complexity Builder** is to provide a Python-based
profiling and complexity-analysis framework that can be attached to a
function through a decorator.

The main objective is to measure what happens during a function
execution and, from those measurements, provide useful information
about:

-   function calls;
-   loops and iterations;
-   recursion;
-   memory usage;
-   allocations;
-   iterators;
-   hotspots;
-   line execution;
-   algorithmic operations;
-   static code structure;
-   estimated algorithmic complexity.

The project should combine **dynamic analysis** (observing a function
while it runs) with **static analysis** (inspecting its source code
before execution).

The main entry point should be a decorator:

``` python
@complexity_monitor
def calculate_series(n):
    total = 0

    for i in range(1, n + 1):
        total += i

    return total
```

The decorator should transparently launch the profiling process around
the target function.

------------------------------------------------------------------------

# Architecture

``` text
                         complexity_monitor
                                  │
                                  ▼
                         ComplexityRunner
                                  │
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
          ▼                       ▼                        ▼
     Execution                 Runtime                  Analysis
      Metrics                  Metrics                  Metrics
          │                       │                        │
          ├── Calls               ├── Memory              ├── Complexity
          ├── Exceptions          ├── Allocations         ├── Big-O
          ├── Recursion           ├── GC                  ├── Loop Analysis
          ├── Loops               ├── I/O                 ├── Hotspots
          └── ...                 └── ...                 └── ...
```

The architecture should keep a clear separation between:

1.  **Trackers**: collect runtime information.
2.  **Analyzers**: interpret collected information.
3.  **Runner**: orchestrates the execution and trackers.
4.  **Report Generator**: aggregates all results into a readable report.
5.  **Decorator**: provides a simple user-facing API.

A tracker should measure data without trying to determine its
algorithmic meaning.

For example:

``` text
LoopTracker
    ↓
10,000 loop iterations
    ↓
ComplexityAnalyzer
    ↓
Estimated complexity: O(n)
```

------------------------------------------------------------------------

# 1. Execution Tracking Scope 

This specification intentionally excludes time-based tracking.

The execution layer focuses on:

-   call counts;
-   loop counts and iterations;
-   recursion depth and recursive call counts;
-   exceptions and control-flow events.

The objective is to keep the first implementation focused on structural
complexity signals rather than timing signals.

------------------------------------------------------------------------

# 2. Loop Tracker

The `LoopTracker` is one of the core components of the project.

Its purpose is to identify and measure loops during execution.

## Number of loops

Example:

``` text
Loops detected : 4
```

## Number of iterations

Example:

``` text
Loop #1 : 10,000
Loop #2 : 10,000
Loop #3 : 100
Loop #4 : 50
```

## Loop depth

For:

``` python
for i in range(n):
    for j in range(n):
        ...
```

the tracker should be able to report:

``` text
Maximum loop depth : 2
```

## Nested loops

The tracker should ideally reconstruct the nesting relationship:

``` text
Loop #1
└── Loop #2
    └── Loop #3
```

## Dominant loops by iterations

Example:

``` text
Loop #1 : 10,000 iterations (12%)
Loop #2 : 72,000 iterations (88%)
```

This information can later be used by the hotspot analysis.

## Iteration distribution

This is particularly useful for `while` loops.

Example:

``` text
Loop #1
Iterations:
  min : 2
  max : 14
  avg : 7.4
```

This can help understand loops whose number of iterations depends on the
input or on runtime conditions.

------------------------------------------------------------------------

# 3. Call Tracker

The `CallTracker` measures function and method calls.

Example:

``` python
def main():
    preprocess()
    calculate()
    postprocess()
```

Possible output:

``` text
Function calls
────────────────────
main()          1
preprocess()    1
calculate()     1
sqrt()          2,000
postprocess()   1
```

## Dynamic call tree

The tracker should ideally reconstruct the dynamic call hierarchy.

Example:

``` text
Call tree

main()
│
├── preprocess()
│   ├── clean()
│   └── normalize()
│
├── calculate()
│   ├── compute()
│   │   └── sqrt()
│   └── compute()
│
└── postprocess()
```

This can eventually become a dynamic call graph.

------------------------------------------------------------------------

# 4. Recursion Tracker

The `RecursionTracker` should be separate from the `CallTracker`.

The `CallTracker` counts function calls in general, while the
`RecursionTracker` focuses specifically on recursive behavior.

## Metrics

It should measure:

-   number of recursive calls;
-   maximum recursion depth;
-   recursive call tree;
-   potentially recursion branching factor.

Example:

``` text
Recursive calls       : 1,023
Maximum recursion     : 11
```

For:

``` python
fib(10)
```

the tool could represent the execution as:

``` text
fib(10)
├── fib(9)
│   ├── fib(8)
│   └── fib(7)
└── fib(8)
```

This information can later help the complexity analyzer identify
potentially exponential behavior.

------------------------------------------------------------------------

# 5. Memory Tracker

The `MemoryTracker` measures memory consumption during execution.

## Metrics

Measure:

-   memory usage at the beginning;
-   memory usage at the end;
-   peak memory;
-   average memory;
-   memory delta;
-   memory usage over time.

Example:

``` text
Memory
────────────────────
Initial       : 12.4 MB
Final         : 14.1 MB
Peak          : 38.7 MB
Delta         : +1.7 MB
```

## Allocation hotspots

The tracker should eventually help answer:

> Which function caused the largest increase in memory usage?

Example:

``` text
Top allocations

calculate()       +12.4 MB
build_matrix()     +8.2 MB
sort_data()        +2.1 MB
```

This information can be integrated into the hotspot analysis.

------------------------------------------------------------------------

# 6. Allocation Tracker

The `AllocationTracker` should be distinguished from the
`MemoryTracker`.

### MemoryTracker

Answers:

> How much memory is being used?

### AllocationTracker

Answers:

> How many objects or memory allocations occurred?

Example:

``` text
Allocations
────────────────────
Objects created : 2,381,421
Objects freed   : 2,380,912
Net             : +509
```

This is particularly useful when comparing two implementations of the
same algorithm.

For example:

``` text
Implementation A
Objects created : 2,381,421

Implementation B
Objects created : 182,421
```

The difference could reveal unnecessary temporary object creation.

------------------------------------------------------------------------

# 7. Iterator Tracker

The `IteratorTracker` focuses on Python iterators and iteration
mechanisms.

For example:

``` python
for x in data:
    ...
```

The tracker could collect information about the iterator being consumed.

Example:

``` text
Iterator
────────────────────
list iterator      : 10,000
generator          : 10,000
range              : 10,000
```

Potential future capabilities:

-   identify iterator types;
-   count iterator consumption;
-   detect generators;
-   detect generators that are consumed;
-   compare eager iteration with lazy iteration;
-   identify repeated consumption of the same iterable.

------------------------------------------------------------------------

# 8. Algorithm Operation Tracker

The `AlgorithmOperationTracker` aims to move closer to algorithmic
analysis.

It could attempt to count elementary operations such as:

``` text
Operations
────────────────────
Addition       : 10,000
Multiplication : 10,000
Comparison     : 20,000
Assignment     : 30,000
```

This could eventually provide an approximation of the number of
operations performed by an algorithm.

However, this component is considerably more complex because operation
counting depends heavily on:

-   Python's runtime;
-   the interpreter;
-   native implementations;
-   libraries;
-   C extensions;
-   vectorized operations;
-   object types.

Therefore, this component should be considered a later-stage feature
rather than part of the initial MVP.

------------------------------------------------------------------------

# 9. Hotspot Tracker

The `HotspotTracker` identifies the parts of the program consuming the
most resources.

## Line hotspots

Example:

``` text
HOTSPOTS
──────────────────────────────
calculate.py:42     64.2%
calculate.py:43     18.7%
parser.py:18         9.4%
utils.py:81          4.1%
```

## Function hotspots

Example:

``` text
Top functions by iteration share

calculate()       64.2%
parse()            18.7%
normalize()         9.4%
```

Potential future hotspot dimensions:

-   memory allocation;
-   number of calls;
-   number of iterations;
-   number of operations.

The goal is to identify the parts of the application where optimization
would have the greatest impact.

------------------------------------------------------------------------

# 10. Line Tracker

The `LineTracker` counts how many times individual source-code lines are
executed.

Example:

``` text
Line execution
────────────────────
Line 10 : 1
Line 11 : 1
Line 12 : 10,000
Line 13 : 10,000
Line 14 : 1
```

This information can be especially useful for the `LoopTracker`.

For example:

``` text
line 12 → 10,000 executions
              ↓
        likely loop body
```

The reporting strategy should avoid overwhelming the user with
information.

Potential filtering rules:

-   hide lines executed only once;
-   hide lines with negligible execution frequency;
-   display only recurrent lines;
-   display the top N most frequently executed lines;
-   adapt the number of displayed lines to the size of the project.

The exact filtering strategy should be investigated during
implementation.

------------------------------------------------------------------------

# 11. Complexity Analyzer

The `ComplexityAnalyzer` should not be implemented as a tracker.

It should operate after the runtime data has been collected.

It consumes observations such as:

``` text
n       loops
10      10
100     100
1000    1000
10000   10000
```

It then attempts to identify the mathematical model that best explains
the observed behavior.

Potential complexity classes:

``` text
O(1)
O(log n)
O(n)
O(n log n)
O(n²)
O(n³)
O(n^k)
O(2^n)
O(k^n)
```

The analyzer could eventually support other models as well.

## Example output

``` text
Estimated complexity
────────────────────────
Iterations : O(n)
Memory     : O(1)

Confidence : 99.2%
```

## Important distinction

The analyzer should clearly distinguish between:

-   measured iteration count;
-   estimated asymptotic complexity.

A single execution cannot reliably establish Big-O complexity.

The tool should therefore run the target function against multiple input
sizes and compare the resulting measurements.

For example:

``` text
n = 10
n = 100
n = 1,000
n = 10,000
```

The analyzer can then fit and compare different candidate models.

------------------------------------------------------------------------

# 12. Static Analyzer

The `StaticAnalyzer` performs analysis before the function is executed.

It should use Python's AST (Abstract Syntax Tree) to inspect the source
code.

Potentially detected structures:

-   `for` loops;
-   `while` loops;
-   `if` conditions;
-   function calls;
-   recursive calls;
-   nested loops;
-   maximum loop depth;
-   potential control-flow structures.

Example:

``` python
for i in range(n):
    for j in range(n):
        ...
```

Possible analysis:

``` text
Static Analysis
────────────────────
Loops              : 2
Nested loops       : 2
Maximum depth      : 2
Recursion          : no

Potential complexity:
O(n²)
```

## Static complexity

The static analyzer should be considered a source-code-based estimation.

For example, two nested loops may suggest:

``` text
Potential complexity: O(n²)
```

but the actual complexity may depend on the bounds of the loops.

Therefore, the result should be described as a **potential complexity**
or **static estimation**, not as a mathematically proven Big-O
classification.

------------------------------------------------------------------------

# 13. Report Generator (DONE)

The `ReportGenerator` aggregates the results produced by the different
trackers and analyzers.

The report should provide a clear overview of the target function.

Example:

``` text
╔════════════════════════════════════════╗
║        COMPLEXITY PROFILER             ║
╠════════════════════════════════════════╣
║ Function : calculate_series             ║
║                                        ║
║ Runtime                                ║
║ └── Memory     : +2.1 MB               ║
║                                        ║
║ Execution                              ║
║ ├── Calls      : 1                     ║
║ ├── Loops      : 2                     ║
║ ├── Iterations : 1,000,000             ║
║ └── Recursion  : 0                     ║
║                                        ║
║ Complexity                             ║
║ ├── Iterations : O(n²)                 ║
║ ├── Space      : O(1)                  ║
║ └── Confidence : 98.7%                 ║
╚════════════════════════════════════════╝
```

The report generator could eventually support multiple output formats:

``` text
CLI
JSON
HTML
Markdown
```

------------------------------------------------------------------------

# 14. Proposed Component Organization

A possible project structure:

``` text
complexity_builder/
│
├── __init__.py
│
├── decorator/
│   └── complexity_monitor.py
│
├── runner/
│   └── complexity_runner.py
│
├── trackers/
│   ├── loop_tracker.py
│   ├── call_tracker.py
│   ├── recursion_tracker.py
│   ├── memory_tracker.py
│   ├── allocation_tracker.py
│   ├── iterator_tracker.py
│   ├── operation_tracker.py
│   ├── hotspot_tracker.py
│   └── line_tracker.py
│
├── analyzers/
│   ├── complexity_analyzer.py
│   └── static_analyzer.py
│
├── models/
│   ├── execution_report.py
│   ├── loop_metrics.py
│   ├── memory_metrics.py
│   └── complexity_metrics.py
│
├── reporting/
│   └── report_generator.py
│
└── cli/
    └── main.py
```

The exact structure can evolve as the project grows.

------------------------------------------------------------------------

# 15. Execution Flow

The intended execution flow is:

``` text
User
 │
 │ @complexity_monitor
 ▼
Complexity Monitor
 │
 ▼
Complexity Runner
 │
 ├── Start trackers
 │
 ├── Run target function
 │
 ├── Collect runtime metrics
 │
 └── Stop trackers
 │
 ▼
Execution Report
 │
 ├── Runtime metrics
 ├── Loop metrics
 ├── Call metrics
 ├── Memory metrics
 └── Other metrics
 │
 ▼
Static Analyzer
 │
 └── Analyze source code
 │
 ▼
Complexity Analyzer
 │
 ├── Analyze input sizes
 ├── Compare measurements
 ├── Test complexity models
 └── Estimate Big-O
 │
 ▼
Report Generator
 │
 ├── CLI
 ├── JSON
 ├── Markdown
 └── HTML
```

------------------------------------------------------------------------

# 16. Decorator API

The simplest user-facing API should remain lightweight.

Example:

``` python
@complexity_monitor
def calculate_series(n):
    total = 0

    for i in range(1, n + 1):
        total += i

    return total
```

The decorator should:

1.  start the profiling process;
2.  execute the original function;
3.  collect the configured metrics;
4.  stop the profiling process;
5.  build the execution report;
6.  return the original function's result.

The decorator should not contain the actual profiling logic.

Instead:

``` text
@complexity_monitor
        │
        ▼
ComplexityRunner
        │
        ├── LoopTracker
        ├── CallTracker
        ├── MemoryTracker
        └── ...
```

This keeps the architecture modular.

------------------------------------------------------------------------

# 17. Builder Concept

A builder can eventually allow users to selectively enable profiling
components.

For example:

``` python
analyzer = (
    ComplexityBuilder()
        .track_loops()
        .track_calls()
        .track_memory()
        .track_allocations()
        .enable_static_analysis()
        .enable_complexity_analysis()
        .build()
)
```

Then:

``` python
@analyzer
def calculate(n):
    ...
```

This approach avoids forcing every tracker to run for every function.

It also allows the user to trade profiling detail for profiling
overhead.