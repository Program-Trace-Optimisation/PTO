[       # problems_sizess_budgetss_ctors
        # each row is (problem_name, sizes, constructor fn given only size)
        ('OneMax', (8, 16, 32), (50, 200, 1000), (lambda s: OneMax(s))),
        ('HelloWorld', (8, 16, 32), (500, 2000, 6000), (lambda s: HelloWorld(target='A'*s))),
        ('Sphere', (8, 16, 32), (100, 500, 5000), (lambda s: Sphere(s))),
        ('TSP', (8, 16, 24), (5000, 50000, 100000), (lambda s: TSP(N=s))), 
        ('SymbolicRegression', (6, 9, 12), (8000, 20000, 100000), (lambda s: SymbolicRegression(s*20, s))), 
        ('GrammaticalEvolution', (3, 6, 9), (2000, 10000, 30000), (lambda s: GrammaticalEvolution(s*20, s))), 
        ('NeuralNetwork', (2, 4, 6), (3000, 10000, 50000), (lambda s: NeuralNetwork(s, int(s*1.5), s, s*20))) # s*1.5 is the max_hidden
]