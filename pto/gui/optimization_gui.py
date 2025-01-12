import ipywidgets as widgets
from IPython.display import display, clear_output
import matplotlib.pyplot as plt
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

        # Optimization settings
        self.optimization_direction = widgets.RadioButtons(
            options=[("Maximize", max), ("Minimize", min)],
            value=max,
            description="Optimize:",
            style={"description_width": "initial"},
            layout={"margin": "10px 0"},
        )

        # Solver parameters definitions
        self.solver_params = {
            "hill_climber": {
                "n_generation": {
                    "value": 1000,
                    "type": int,
                    "min": 1,
                    "description": "Number of generations",
                },
                "mutation": {
                    "value": "mutate_position_wise_ind",
                    "type": str,
                    "options": [
                        "mutate_position_wise_ind",
                        "mutate_point_ind",
                        "mutate_random_ind",
                    ],
                    "description": "Mutation operator",
                },
            }
        }

        # Create solver choice dropdown
        self.solver_choice = widgets.Dropdown(
            options=["hill_climber"],
            value="hill_climber",
            description="Solver:",
            style={"description_width": "initial"},
            layout={"width": "auto", "margin": "10px 0"},
        )

        # Create parameters section
        self.show_params = widgets.Checkbox(
            value=False,
            description="Show Solver Parameters",
            layout={"margin": "10px 0"},
        )

        # Parameters output area
        self.params_box = widgets.VBox([])
        self.current_param_widgets = {}

        # Create parameter widgets for initial solver
        self._create_param_widgets()

        # Update parameters when solver changes
        self.solver_choice.observe(self._on_solver_change, names="value")
        self.show_params.observe(self._toggle_params, names="value")

        # Create buttons
        self.start_button = widgets.Button(
            description="Start Optimization",
            button_style="success",
            layout={"width": "auto"},
        )
        self.start_button.on_click(self.run_optimization)

        self.stop_button = widgets.Button(
            description="Stop Optimization",
            button_style="danger",
            layout={"width": "auto"},
            disabled=True,
        )
        self.stop_button.on_click(self.stop_optimization)

        # Create button box
        self.button_box = widgets.HBox(
            [self.start_button, self.stop_button], layout={"gap": "10px"}
        )

        # Create output areas with wider layout
        self.output = widgets.Output(
            layout={
                "width": "100%",  # Changed from 50% to 100%
                "height": "300px",
                "border": "1px solid #ddd",
                "overflow": "auto",  # Added scrolling
            }
        )
        self.progress_output = widgets.Output(
            layout={
                "width": "100%",  # Changed from 50% to 100%
                "height": "300px",
                "border": "1px solid #ddd",
            }
        )

        # Create horizontal box for output and progress with flex layout
        self.results_box = widgets.HBox(
            [
                widgets.VBox(
                    [widgets.HTML("<h4>Output:</h4>"), self.output],
                    layout=widgets.Layout(flex="1"),
                ),  # Added flex
                widgets.VBox(
                    [widgets.HTML("<h4>Progress:</h4>"), self.progress_output],
                    layout=widgets.Layout(flex="1"),
                ),  # Added flex
            ],
            layout=widgets.Layout(width="100%"),  # Ensure full width
        )

        # Settings box
        self.settings_box = widgets.VBox(
            [
                widgets.HTML("<h4>Optimization Settings:</h4>"),
                self.optimization_direction,
                self.solver_choice,
                self.show_params,
                self.params_box,
            ],
            layout={"padding": "10px", "border": "1px solid #ddd", "margin": "10px 0"},
        )

        # Create tabs
        self.code_tab = widgets.VBox(
            [
                widgets.HTML("<p>Generator Function:</p>"),
                self.generator_code,
                widgets.HTML("<p>Fitness Function:</p>"),
                self.fitness_code,
            ]
        )

        self.settings_tab = widgets.VBox([self.settings_box])

        self.tabs = widgets.Tab()
        self.tabs.children = [self.code_tab, self.settings_tab]
        self.tabs.set_title(0, "Code")
        self.tabs.set_title(1, "Optimization Settings")

        # Layout all components
        self.gui = widgets.VBox(
            [
                widgets.HTML("<h3>Optimization Framework</h3>"),
                self.tabs,
                self.button_box,
                self.results_box,
            ],
            layout=widgets.Layout(width="100%"),
        )

        # Initialize progress tracking
        self.fitness_history = []
        self.should_stop = False
        self.update_interval = 10  # Update graph every 10 generations
        self.fig = None  # Store figure reference
        self.ax = None  # Store axes reference

    def _create_param_widgets(self):
        """Create widgets for the current solver's parameters"""
        self.current_param_widgets = {}
        solver = self.solver_choice.value
        widgets_list = []

        for param_name, param_info in self.solver_params[solver].items():
            if param_info["type"] == int:
                widget = widgets.IntText(
                    value=param_info["value"],
                    description=param_name,
                    min=param_info.get("min", None),
                    style={"description_width": "initial"},
                    layout={"width": "auto"},
                )
            elif param_info["type"] == bool:
                widget = widgets.Checkbox(
                    value=param_info["value"],
                    description=param_name,
                    layout={"width": "auto"},
                )
            elif param_info["type"] == str and "options" in param_info:
                widget = widgets.Dropdown(
                    options=param_info["options"],
                    value=param_info["value"],
                    description=param_name,
                    style={"description_width": "initial"},
                    layout={"width": "auto"},
                )

            widgets_list.append(widget)
            self.current_param_widgets[param_name] = widget

        self.params_box.children = widgets_list

    def _on_solver_change(self, change):
        """Handle solver selection change"""
        self._create_param_widgets()

    def _toggle_params(self, change):
        """Toggle parameter visibility"""
        self.params_box.layout.display = "block" if change["new"] else "none"

    def create_function(self, code_str, func_name):
        """Create a function with source code accessible via __code__ attribute"""
        namespace = {}
        exec(code_str, namespace)
        func = namespace[func_name]

        new_func = types.FunctionType(
            func.__code__,
            func.__globals__,
            func_name,
            func.__defaults__,
            func.__closure__,
        )

        setattr(new_func, "_source_code", textwrap.dedent(code_str))

        def get_source(obj):
            return obj._source_code

        import inspect

        inspect.getsource = get_source

        return new_func

    def stop_optimization(self, _):
        """Handler for stop button click"""
        self.should_stop = True
        self.stop_button.disabled = True
        with self.output:
            print("\nStopping optimization...")

        # Set default example code
        self.generator_code.value = """def generator():
    return [rnd.uniform(-10, 10) for _ in range(5)]"""

        self.fitness_code.value = """def fitness(solution):
    return -sum(x**2 for x in solution)  # Simple negative sum of squares"""

    def update_progress(self, search_state):
        """Updated callback that reduces flickering and improves performance"""
        individual, fitness, generation = search_state
        self.fitness_history.append(fitness)

        if self.should_stop:
            return True

        if generation % self.update_interval == 0:
            with self.progress_output:
                if generation == 0:
                    # Initialize plot on first update
                    clear_output(wait=True)
                    self.fig, self.ax = plt.subplots(figsize=(8, 5))
                    plt.close()  # Close the initial blank figure

                # Update existing plot instead of creating new one
                if self.ax is not None:
                    self.ax.clear()
                    self.ax.plot(self.fitness_history, "-b", label="Best Fitness")
                    self.ax.grid(True)
                    self.ax.set_xlabel("Generation")
                    self.ax.set_ylabel("Fitness")
                    self.ax.set_title(
                        f"Optimization Progress (Generation {generation})"
                    )
                    self.ax.legend()

                    # Only update display, don't clear
                    clear_output(wait=True)
                    display(self.fig)

                    # Print status below plot
                    print(f"\nGeneration: {generation}")
                    print(f"Current Fitness: {fitness}")

        return False
