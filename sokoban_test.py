import sokoban

with open("GameStateSamples/sokoban001") as gameFile:
    gameStr = gameFile.read()

soko = sokoban.Sokoban.getStateFromString(gameStr)


assert str(soko) == gameStr, "String did not match initial state"

state = soko.initialGameState
assert soko.isLegal(soko.initialGameState) is True, "Game is legal"

state.robot = (0, 0)
assert soko.isLegal(state) is False, "Game is illegal"

state = soko.initialGameState
assert len(soko.successors(state)) == 2, "Gets next legal moves"

state = sokoban.GameState(robot=(6, 3), boxes=soko.storage)
assert soko.isWon(state), "Game is won"

print("!!!All tests passed!!!")
