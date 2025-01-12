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

        # Create output areas
        self.output = widgets.Output(
            layout={"width": "50%", "height": "300px", "border": "1px solid #ddd"}
        )
        self.progress_output = widgets.Output(
            layout={"width": "50%", "height": "300px", "border": "1px solid #ddd"}
        )

        # Create horizontal box for output and progress
        self.results_box = widgets.HBox(
            [
                widgets.VBox([widgets.HTML("<h4>Output:</h4>"), self.output]),
                widgets.VBox(
                    [widgets.HTML("<h4>Progress:</h4>"), self.progress_output]
                ),
            ]
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

        # Set default example code
        self.generator_code.value = """def generator():
    return [rnd.uniform(-10, 10) for _ in range(5)]"""

        self.fitness_code.value = """def fitness(solution):
    return -sum(x**2 for x in solution)  # Simple negative sum of squares"""

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

    def update_progress(self, search_state):
        """Default callback that plots optimization progress with minimal overhead
        Args:
            search_state: tuple of (individual, fitness, generation)
        Returns:
            bool: True to stop optimization, False to continue
        """
        individual, fitness, generation = search_state
        self.fitness_history.append(fitness)

        # Check for stop condition immediately
        if self.should_stop:
            return True

        # Update graph less frequently and only if not stopping
        if generation % self.update_interval == 0:
            with self.progress_output:
                clear_output(wait=True)

                # Print current state (faster than plotting)
                print(f"Generation {generation}")
                print(f"Current Fitness: {fitness}")

                # Only plot if we have enough new data points
                if generation > 0:  # Skip first plot
                    plt.figure(figsize=(6, 4))
                    plt.plot(self.fitness_history, "-b", label="Best Fitness")
                    plt.grid(True)
                    plt.xlabel("Generation")
                    plt.ylabel("Fitness")
                    plt.title(f"Optimization Progress (Generation {generation})")
                    plt.legend()
                    plt.tight_layout()
                    plt.show()
                    plt.close()  # Explicitly close the figure

        return False

    def run_optimization(self, _):
        # Reset stop flag and update button states
        self.should_stop = False
        self.start_button.disabled = True
        self.stop_button.disabled = False

        with self.output:
            clear_output()
            try:
                # Reset fitness history
                self.fitness_history = []

                # Create functions
                generator = self.create_function(
                    self.generator_code.value.strip(), "generator"
                )
                fitness = self.create_function(
                    self.fitness_code.value.strip(), "fitness"
                )

                # Collect solver parameters
                solver_args = {
                    name: widget.value
                    for name, widget in self.current_param_widgets.items()
                }

                # Run optimization
                from pto.core.automatic_names.trans_run import run

                solution = run(
                    Gen=generator,
                    Fit=fitness,
                    better=self.optimization_direction.value,
                    Solver="hill_climber",
                    solver_args=solver_args,
                    callback=self.update_progress,  # Make sure callback is passed
                )

                if self.should_stop:
                    print("\nOptimization stopped by user.")
                else:
                    print("\nOptimization complete!")
                print("Solution:", solution)

            except Exception as e:
                print("Error occurred:")
                print(traceback.format_exc())
            finally:
                # Reset button states
                self.start_button.disabled = False
                self.stop_button.disabled = True
                self.should_stop = False

    def display(self):
        """Display the GUI"""
        display(self.gui)
