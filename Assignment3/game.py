import random

action = ['ROCK', 'PAPER', 'SCISSORS']
oppositeMove = [1, 2, 0]

class Game:
    def __init__(self, name):
        self.name = name
        self.hand = -1
        self.moveType = 'RANDOM'
        self.score = 0
        self.opponentHand = -1

    def copy(self,game):
        self.hand = game.hand
        self.moveType = game.moveType
        self.score = game.score
        self.opponentHand = game.opponentHand

    def play(self):
        pass

    def displayResult(self):
        print(f'{self.name}\'s score is {self.score}')

    def updateScore(self, opponentHand):
        self.opponentHand = opponentHand
        if self.hand == opponentHand:
            print(f'{self.name} played {action[self.hand]}: DRAW')
        elif self.hand == oppositeMove[opponentHand]:
            self.score += 1
            print(f'{self.name} played {action[self.hand]}: WON')
        else:
            print(f'{self.name} played {action[self.hand]}: LOST')
            
class RandomGame(Game):
    def __init__(self,game):
        super().__init__(game.name)
        self.copy(game)

    def play(self):
        self.moveType = 'RANDOM'
        self.hand = random.randint(0,2)

class MirrorGame(Game):
    def __init__(self,game):
        super().__init__(game.name)
        self.copy(game)

    def play(self):
        if self.opponentHand == -1:
            raise Exception('MIRROR move not possible now.\n')
        self.moveType = 'MIRROR'
        self.hand = oppositeMove[self.opponentHand]

if __name__ == '__main__':
    print('Welcome to the Rock-Paper-Scissiors game.\n')
    game = [Game('Player1'), Game('Player2')]

    while(True):
        print(f'Press 1 to play again, 2 to display current result and 3 to exit\n')
        opr = int(input())

        if opr == 1:
            for player in [0,1]:
                try:
                    print(f'Player{player+1} Select move type:')
                    print(f'Press 1 for RANDOM')
                    print(f'Press 2 for MIRROR')
                    opr = int(input())

                    if opr not in [1,2]:
                        raise Exception('Invalid move\n')
                    
                    if opr == 1:
                        game[player] = RandomGame(game[player])
                    else:
                        game[player] = MirrorGame(game[player])
                    game[player].play()
                    print('\n')
                except Exception as e:
                    print(e)
            game[0].updateScore(game[1].hand)
            game[1].updateScore(game[0].hand)
            print('\n')
            
        elif opr == 2:
            for player in [0,1]:
                game[player].displayResult()
            print('\n')
        elif opr == 3:
            for player in [0,1]:
                game[player].displayResult()
            print(f'Thank you for playing!\n')
            break
        else:
            print('Invalid input\n')
