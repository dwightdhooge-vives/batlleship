from random import randint, shuffle
from IPython.display import clear_output
from flask_ngrok import run_with_ngrok
from flask import Flask, request


def configure(grid_dim, boat_length, bombs):
    # boat cannot be longer than grid dimension
    if boat_length > grid_dim:
        print("Boat too long!")
        return {}
    # boat length is ok!
    else:
        battleship = {
            'grid_dim': grid_dim,
            'boat_length': boat_length,
            'bombs': bombs,
            'bombs_left': bombs,
            'hit': False,
            'sunk': False,
        }
        return battleship


def create_grid(battleship):
    # initialize grid with zeros
    n = battleship['grid_dim']
    battleship['grid'] = [[0 for column in range(n)] for row in range(n)]


def position_boat(battleship):
    # initialize
    n = battleship['grid_dim']
    boat = [[False for column in range(n)] for row in range(n)]

    # first cell
    n -= 1
    row = randint(0, n)
    column = randint(0, n)
    boat[row][column] = True

    # shuffle directions
    directions = [0, 1, 2, 3]  # 0=N, 1=O, 2=Z, 3=W
    shuffle(directions)

    # others cells
    j = battleship['boat_length'] - 1
    for d in directions:
        if (d == 0) and ((row - j) >= 0):
            for i in range(row - j, row):
                boat[i][column] = True
            break
        elif (d == 1) and ((column + j) <= n):
            for i in range(column + 1, column + j + 1):
                boat[row][i] = True
            break
        elif (d == 2) and ((row + j) <= n):
            for i in range(row + 1, row + j + 1):
                boat[i][column] = True
            break
        elif (d == 1) and ((column - j) >= 0):
            for i in range(column - j, column):
                boat[row][i] = True
            break

    # add to battleship dictionary
    battleship['boat'] = boat


def initialize(grid_dim, boat_length, bombs):
    battleship = configure(grid_dim, boat_length, bombs)
    create_grid(battleship)
    position_boat(battleship)
    return battleship


def drop_bomb(battleship, row, column):
    battleship['bombs_left'] -= 1
    battleship['hit'] = battleship['boat'][row][column]
    battleship['grid'][row][column] = 1 if battleship['hit'] else -1
    if battleship['hit']:
        hits = sum([column for row in battleship['grid'] for column in row if column == 1])
        battleship['sunk'] = hits == battleship['boat_length']


def grid_to_string(battleship, is_html=False):
    # html? use <br> instead of \n
    newline = '<br>' if is_html else '\n'
    spaces = '&nbsp;' * 2 if is_html else '  '

    # grid and its dimension
    grid = battleship['grid']
    n = battleship['grid_dim']

    # column numbers
    numbers = [str(i) for i in range(n)]
    grid_string = [spaces + " ".join(numbers)]

    # rows
    for i in range(n):
        row = ["." if column == 0 else "x" if column == 1 else "o" for column in grid[i]]
        grid_string.append(numbers[i] + " " + " ".join(row))
    grid_string = newline.join(grid_string) + newline

    # hmtl? define font
    if is_html:
        grid_string = f'<p style="font-family:\'Courier New\'; font-weight: bold; font-size:30px">{grid_string}</p>'

    # output grid string
    return grid_string


def message(battleship, is_html=False):
    # string indicating the number of bombs that are left
    bombs_left = battleship['bombs_left']
    bomb_string = f"{bombs_left} bomb" + ("s" if bombs_left > 1 else "")

    # no bombs dropped yet: start of the game
    if bombs_left == battleship['bombs']:
        msg = f"You have {bomb_string} to destroy the submarine. Good hunting!"

    # boot is gezonken:
    elif battleship['sunk']:
        msg = "Congrats!! The submarine has been destroyed!"

    # all bombs are dropped and the boat has not sunk
    elif bombs_left == 0:
        msg = "No more bombs and the submarine is still cruising..."

    # bombs left and the boat is still cruising
    else:
        msg = ("Hit!!" if battleship['hit'] else "Miss!") + f" You have {bomb_string} left..."

    # add newline
    if is_html:
        msg = f'<p><br>{msg}</p>'
    else:
        msg = '\n' + msg

    # output string
    return msg


def game_display(battleship, is_html=False):
    return grid_to_string(battleship, is_html) + message(battleship, is_html)


def cli(battleship):
    # print display
    print(game_display(battleship))

    # ask for input while bombs left and boat has not sunk
    while battleship['bombs_left'] > 0 and not battleship['sunk']:
        # player's input: row and column
        row = int(input("Rij: "))
        column = int(input("Column: "))

        # drop bomb
        drop_bomb(battleship, row, column)

        # clear previous display and print new one
        clear_output(wait=True)
        print(game_display(battleship))


def html_form():
    # HTML form
    return """
  <form method="post">
  <label for="row">Row:</label>
  <input type="text" name="row" autofocus><br><br>
  <label for="column">Column:</label>
  <input type="text" name="column"><br><br>
  <button type="submit">Submit</button>
  </form>
  """


def web(battleship):
    # create WSGI server app
    app = Flask(__name__)
    run_with_ngrok(app)

    # function that creates HTML for client browser
    # as response to HTTP requests GET en POST
    #   GET: start of the game
    #   POST: player drops bomb by submitting row en column
    @app.route('/', methods=('GET', 'POST'))
    def create_html():

        # GET: display situation at start of game
        if request.method == 'GET':

            print(game_display(battleship))
            html = game_display(battleship, is_html=True) + html_form()

        # POST: player drops bomb
        else:

            # input row and column
            row = int(request.form['row'])
            column = int(request.form['column'])
            print(row, column)

            # drop bomb and display
            drop_bomb(battleship, row, column)
            print(game_display(battleship))
            html = game_display(battleship, is_html=True)

            # game over -> shut down server
            if battleship['bombs_left'] == 0 or battleship['sunk']:
                request.environ.get('werkzeug.server.shutdown')()

            # game not over yet -> add form
            else:
                html += html_form()

        # return html string
        return html

    # run server app
    app.run()


def play(grid_dim, boat_length, bombs, online=False):
    # initialize game
    battleship = initialize(grid_dim, boat_length, bombs)

    # play game online
    if online:
        web(battleship)

    # play game in Python shell
    else:
        cli(battleship)

