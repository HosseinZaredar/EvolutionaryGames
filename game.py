import pygame
import time
import random
import argparse

from player import Player
from box_list import BoxList
from evolution import Evolution
from config import CONFIG
from util import save_generation, load_generation

# argument parser
parser = argparse.ArgumentParser(
    description='Parser',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument(
    '--play',
    type=str,
    default='False',
    choices=['False', 'True'],
)

parser.add_argument(
    '--mode',
    type=str,
    default='helicopter',
    choices=['gravity', 'helicopter', 'thrust'],
)

parser.add_argument(
    '--checkpoint',
    type=str,
    default='',
)

args = parser.parse_args()


class Game():

    def __init__(self):  # class initializer

        self.screen = pygame.display.set_mode((CONFIG['WIDTH'], CONFIG['HEIGHT']))
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 26)
        self.speed_font = pygame.font.SysFont("Arial", 42)
        self.camera = 0

    def run(self, mode, checkpoint_path):  # a function to run the game in evolutionary mode

        clock = pygame.time.Clock()
        evolution = Evolution(mode)  # evolutionary algorithms are implemented in this class

        background, box_img, agent = self.load_images(mode)  # load images
        agent_counter = 0  # for helicopter mode only

        # game starts from generation 0
        if checkpoint_path == '':
            num_alive = CONFIG['num_players']
            players = evolution.generate_new_population(CONFIG['num_players'])  # players of the current generation
            prev_players = []  # players of the previous generation
            gen_num = 1
            high_score = 0

        # game starts from checkpoint generation (e.g., 20)
        else:
            num_alive = 2 * CONFIG['num_players']
            prev_players = load_generation(checkpoint_path)  # players of the previous generation
            players = evolution.generate_new_population(CONFIG['num_players'], prev_players)  # players of the current generation
            gen_num = int(checkpoint_path[checkpoint_path.rfind('/') + 1:]) + 1
            high_score = max(p.fitness for p in prev_players)

        delta_xs = [0 for _ in range(CONFIG['num_players'])]  # distance travelled by agent
        prev_delta_xs = [0 for _ in range(CONFIG['num_players'])]  # distance travelled by previous generation agents
        prev_alive = [True for _ in range(CONFIG['num_players'])]  # array of previous players' alive status

        box_lists = []

        game_speed = 1
        t = time.time() - CONFIG['box_gap'] / (game_speed * CONFIG['camera_speed'])
        show_fps = False

        show_single = False  # shows only a single agent of the current generation, if True

        random.seed(CONFIG['seed'])

        frame_counter = 0

        # game loop
        while True:

            events = pygame.event.get()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                break

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_d:
                        game_speed = 2 if game_speed == 1 else 1
                    elif event.key == pygame.K_s:
                        show_single = not show_single
                    elif event.key == pygame.K_f:
                        show_fps = not show_fps

            dt = clock.tick(game_speed * CONFIG['fps'])
            self.camera += CONFIG['camera_speed']

            # generates new obstacles
            if time.time() - t > CONFIG['box_gap'] / (game_speed * CONFIG['camera_speed']):
                gap_num = 4
                gap_offset = random.randint(1, 5)
                box_lists.append(self.generate_gap_boxes(gap_num, gap_offset))
                t = time.time()

            if len(box_lists) != 0:
                if box_lists[0].x - self.camera < -60:
                    box_lists.pop(0)

            # move and check collision (current generation agents)
            for i, p in enumerate(players):
                if delta_xs[i] == 0:
                    collided = p.move(box_lists[:4], self.camera)
                    if collided or self.camera > high_score + 10000:
                        delta_xs[i] = self.camera
                        num_alive -= 1

            # move and check collision (previous generation agents)
            for i, p in enumerate(prev_players):
                if prev_alive[i]:
                    collided = p.move(box_lists[:4], self.camera)
                    if collided or self.camera > high_score + 10000:
                        prev_delta_xs[i] = self.camera
                        prev_alive[i] = False
                        num_alive -= 1

            # end of episode
            if num_alive == 0:

                gen_num += 1
                box_lists = []
                high_score = max(max(delta_xs), max(prev_delta_xs), high_score)

                # calculate fitness of current and previous agents
                evolution.calculate_fitness(players, delta_xs)
                evolution.calculate_fitness(prev_players, prev_delta_xs)

                # selection
                prev_players = evolution.next_population_selection(prev_players + players, CONFIG['num_players'])
                for p in prev_players:
                    p.reset_values()
                prev_alive = [True for _ in range(CONFIG['num_players'])]

                self.camera = 0

                # create new population
                players = evolution.generate_new_population(CONFIG['num_players'], prev_players)
                num_alive = 2 * CONFIG['num_players']

                delta_xs = [0 for _ in range(CONFIG['num_players'])]
                prev_delta_xs = [0 for _ in range(CONFIG['num_players'])]
                t = time.time() - CONFIG['box_gap'] / (game_speed * CONFIG['camera_speed'])

                random.seed(CONFIG['seed'])

                # save generations to file
                if gen_num % CONFIG['checkpoint_freq'] == 0:
                    save_generation(prev_players, gen_num, mode)

                continue

            # rendering
            if frame_counter == 0:

                self.screen.blit(background, [0, 0])  # rendering background

                # rendering multi agent
                if not show_single:
                    for i, player in enumerate(players):
                        if delta_xs[i] == 0:
                            if mode == 'helicopter':
                                self.screen.blit(agent[agent_counter], player.pos)
                                agent_counter = (agent_counter + 1) % 4
                            else:
                                self.screen.blit(agent, player.pos)

                    for i, player in enumerate(prev_players):
                        if prev_alive[i]:
                            if mode == 'helicopter':
                                self.screen.blit(agent[agent_counter], player.pos)
                                agent_counter = (agent_counter + 1) % 4
                            else:
                                self.screen.blit(agent, player.pos)

                # rendering single agent
                else:

                    best_player = None

                    for i in range(len(prev_players)):
                        if prev_alive[i]:
                            best_player = prev_players[i]
                            break

                    if best_player == None:
                        for i in range(len(players)):
                            if delta_xs[i] == 0:
                                best_player = players[i]
                                break

                    if mode == 'helicopter':
                        self.screen.blit(agent[agent_counter], best_player.pos)
                        agent_counter = (agent_counter + 1) % 4
                    else:
                        self.screen.blit(agent, best_player.pos)

                # rendering obstacles
                for box_list in box_lists:
                    for box in box_list.boxes:
                        self.screen.blit(box_img, [box[0] - self.camera, box[1]])

                # stats color
                if mode == 'helicopter':
                    color = (0, 0, 0)
                elif mode == 'gravity':
                    color = (255, 255, 255)
                elif mode == 'thrust':
                    color = (0, 0, 0)

                # rendering stats
                self.screen.blit(self.font.render("Generation: " + str(gen_num), -1, color), (25, 20))
                self.screen.blit(self.font.render("Count: " + str(num_alive), -1, color), (25, 60))
                self.screen.blit(self.font.render("High Score: " + str(max(high_score, self.camera)), -1, color),
                                 (225, 20))
                self.screen.blit(self.font.render("Score: " + str(self.camera), -1, color), (225, 60))
                if game_speed == 2:
                    self.screen.blit(self.speed_font.render('2x', -1, color), (1200, 20))

                if show_fps:
                    self.screen.blit(self.speed_font.render(f'{str(1000 // (dt * game_speed))}', -1, color), (1200, 650))

                pygame.display.update()

            frame_counter = (frame_counter + 1) % game_speed

    def play(self, mode):  # a function to run the game in playing mode

        clock = pygame.time.Clock()

        background, box_img, agent = self.load_images(mode)  # load images
        agent_counter = 0  # for helicopter mode only

        player = Player(control=True, mode=mode)

        box_lists = []

        random.seed(CONFIG['seed'])

        t = time.time() - CONFIG['box_gap'] / CONFIG['camera_speed']
        show_fps = False

        high_score = 0

        # game loop
        while True:
            
            events = pygame.event.get()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                break

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        show_fps = not show_fps

            dt = clock.tick(CONFIG['fps'])
            self.camera += CONFIG['camera_speed']

            # generates new obstacles
            if time.time() - t > CONFIG['box_gap'] / CONFIG['camera_speed']:
                gap_num = 4
                gap_offset = random.randint(1, 5)
                box_lists.append(self.generate_gap_boxes(gap_num, gap_offset))
                t = time.time()

            if len(box_lists) != 0:
                if box_lists[0].x - self.camera < -60:
                    box_lists.pop(0)

            collided = player.move(box_lists[:2], self.camera, events)  # move and check collision

            # end of episode
            if collided:
                box_lists = []
                high_score = max(self.camera, high_score)
                self.camera = 0
                player = Player(mode, control=True)
                t = time.time() - CONFIG['box_gap'] / CONFIG['camera_speed']
                random.seed(CONFIG['seed'])

            self.screen.blit(background, [0, 0])  # rendering background

            # rendering agent
            if mode == 'helicopter':
                self.screen.blit(agent[agent_counter], player.pos)
                agent_counter = (agent_counter + 1) % 4
            else:
                self.screen.blit(agent, player.pos)

            # rendering obstacles
            for box_list in box_lists:
                for box in box_list.boxes:
                    self.screen.blit(box_img, [box[0] - self.camera, box[1]])

            # stats color
            if mode == 'helicopter':
                color = (0, 0, 0)
            elif mode == 'gravity':
                color = (255, 255, 255)
            elif mode == 'thrust':
                color = (255, 255, 255)

            # rendering stats
            self.screen.blit(self.font.render("High Score: " + str(high_score), -1, color), (25, 20))
            self.screen.blit(self.font.render("Score: " + str(self.camera), -1, color), (25, 60))
            if show_fps:
                self.screen.blit(self.speed_font.render(f'{str(1000 // dt)}', -1, color), (1200, 650))
            
            pygame.display.update()


    def load_images(self, mode):
        background = pygame.image.load(f'sprites/back_{mode}.jpg').convert()
        background = pygame.transform.scale(background, (1280, 720))

        box_img = pygame.image.load(f'sprites/box_{mode}.png').convert()
        box_img = pygame.transform.scale(box_img, (60, 60))

        if mode == 'helicopter':
            agent_counter = 0
            agent = [pygame.image.load(f'sprites/heli-{i + 1}.png').convert_alpha() for i in range(4)]
            for i in range(4):
                agent[i] = pygame.transform.scale(agent[i], (140, 60))

        elif mode == 'gravity':
            agent = pygame.image.load('sprites/ball_gravity.png').convert_alpha()
            agent = pygame.transform.scale(agent, (80, 80))

        elif mode == 'thrust':
            agent = pygame.image.load('sprites/ball_thrust.png').convert_alpha()
            agent = pygame.transform.scale(agent, (140, 80))

        return background, box_img, agent

    def generate_gap_boxes(self, gap_num, gap_offset):

        vector = []
        for i in range(CONFIG['HEIGHT'] // 60):
            val = 1 if (gap_offset > i) or ((gap_offset + gap_num) <= i) else 0
            vector.append(val)

        box_list = BoxList(gap_num, gap_offset, vector, self.camera)

        return box_list


if __name__ == '__main__':
    is_play = True if args.play == 'True' else False 
    if is_play:
        Game().play(args.mode)
    else:
        Game().run(args.mode, args.checkpoint)
