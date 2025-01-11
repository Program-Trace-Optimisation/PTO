# File: pto/gui/optimization_gui.py

import ipywidgets as widgets
from IPython.display import display, clear_output
import traceback
import types
import textwrap


class OptimizationGUI:
    def __init__(self):
        # Create text areas for code input
        self.generator_code = widgets.Textarea(
            description="Generator:",
            placeholder="def generator():\n    # Your generator code here\n    return candidate_solution",
            layout={"width": "auto", "height": "200px"},
        )

        self.fitness_code = widgets.Textarea(
            description="Fitness:",
            placeholder="def fitness(solution):\n    # Your fitness function code here\n    return fitness_value",
            layout={"width": "auto", "height": "200px"},
        )

        # Create start button
        self.start_button = widgets.Button(
            description="Start Optimization",
            button_style="success",
            layout={"width": "auto"},
        )
        self.start_button.on_click(self.run_optimization)

        # Create output area
        self.output = widgets.Output()

        # Layout all components
        self.gui = widgets.VBox(
            [
                widgets.HTML("<h3>Optimization Framework</h3>"),
                widgets.HTML("<p>Generator Function:</p>"),
                self.generator_code,
                widgets.HTML("<p>Fitness Function:</p>"),
                self.fitness_code,
                self.start_button,
                widgets.HTML("<h4>Output:</h4>"),
                self.output,
            ],
            layout=widgets.Layout(width="100%"),
        )

        # Set default example code
        self.generator_code.value = """def generator():
    return [rnd.uniform(-10, 10) for _ in range(5)]"""

        self.fitness_code.value = """def fitness(solution):
    return -sum(x**2 for x in solution)  # Simple negative sum of squares"""

    def create_function(self, code_str, func_name):
        """Create a function with source code accessible via __code__ attribute"""
        # Define the function in a clean namespace
        namespace = {}
        exec(code_str, namespace)
        func = namespace[func_name]

        # Create a new function that matches the original
        new_func = types.FunctionType(
            func.__code__,
            func.__globals__,
            func_name,
            func.__defaults__,
            func.__closure__,
        )

        # Store the source code directly on the function
        setattr(new_func, "_source_code", textwrap.dedent(code_str))

        # Override the inspect.getsource for this function
        def get_source(obj):
            return obj._source_code

        import inspect

        inspect.getsource = get_source

        return new_func

    def run_optimization(self, _):
        with self.output:
            clear_output()
            try:
                # Create the generator function
                generator = self.create_function(
                    self.generator_code.value.strip(), "generator"
                )

                # Create the fitness function
                fitness = self.create_function(
                    self.fitness_code.value.strip(), "fitness"
                )

                # Run the optimization
                from pto.core.automatic_names.trans_run import run  # , rnd

                solution = run(generator, fitness)

                print("\nOptimization complete!")
                print("Solution:", solution)

            except Exception as e:
                print("Error occurred:")
                print(traceback.format_exc())

    def display(self):
        """Display the GUI"""
        display(self.gui)
