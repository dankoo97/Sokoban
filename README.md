## Sokoban

Sokoban is a game where a player tries to push boxes onto storage spaces

### How to run

```
py main.py <input_game_state> 
    [OPTIONAL animate compare output=<output_file> animationSpeed=<num> maxFringe=<int>] 
    algorithm=<used_algorithm_1> [algorithm_options_and_heuristics ...]
    algorithm=<used_algorithm_2> [algorithm_options_and_heuristics ...]
    ...
```

**EXAMPLE**:
`py main.py ./GameStateSamples/sokoban001 output=game001 compare algorithm=astar bidirectional manhattan isstuck tobox algorithm=bfs`

#### OPTIONS:
* _input_game_state_: **REQUIRED** a file containing the starting game state
* _animate_: displays in the console an animated version
* _compare_: prints to the output file or console a step by step comparison of each algorithm used and completed
* _animationSpeed_: a number representing the "frames" per second for the animation; does nothing if animate is not called; defaults to 3
* _maxFringe_: The maximum total fringe size, defaults to infinite
* _output_file_: The specified output file, defaults to stdout

#### ALGORITHMS:

Requires 1 or more algorithms (not case-sensitive)
* _bfs_: Breadth first search, uses no heuristics, can be run bidirectionally
* _dfs_: Depth first search, uses no heuristics, can be run bidirectionally, but might not be more efficient
* _greedybest_: Greedy Best First search, must be given heuristic, can be run bidirectionally,
* _astar_: A*, without a given heuristic this acts like BFS, can be run bidirectionally

#### ALGORITHM MODIFIERS:

These need to be called after their related algorithm so that the program knows which algorithm to modify
(not case-sensitive)
* _bidirectional_: Run the search bidirectionally
* _manhattan_: Use manhattan distance heuristic from each box to the closest storage spot
* _isStuck_: Use a heuristic that gives an arbitrarily large value when a box is stuck in a corner
* _toBox_: Use manhattan distance heuristic from the player to the nearest box
* _minMatch_: Finds the minimum cost perfect matching of boxes and storage for the manhattan distance (uses numpy)

### Return results

Depending on the given options, the program will return
1. An output statement to the console as each algorithm finishes
2. An animation in the console of each completed path if it exists for each algorithm
3. A comparison chart of each completed path at the specified output location with a step count
4. Stats for each algorithm run

### Comparison chart

When given the option _compare_ the program will print a comparison chart for all completed games. \
This chart will show each game state in each algorithm in order with a step counter. \
Completed games will continue to be shown as completed until all game states reach their conclusion.

### Stats

On completion the program will output information and stats for each algorithm. This includes:
* Whether the algorithm found a solution
* The number of unique states seen
* An upper bound of unique states
* The maximum fringe size used
* The total time passed during the search
* The final path length, 0 if no solution is found
* The used algorithm
* The used heuristics if any
* Whether the search was bidirectional
* The average time per each unique state searched

### Notes

* Bidirectional search is messy, sometimes it returns a slightly less than optimal solution
* Adding new heuristics should be relatively easy with class inheritance
* Min match takes advantage of numpy arrays, which can be installed by `pip install numpy`