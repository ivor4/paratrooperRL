import pygame
import random
import numpy as np
from paratroopergame_objects import *


GAME_MODE_NORMAL = 0
GAME_MODE_EXT_ACTION = 1

# Action values
ACTION_NONE = 0
ACTION_SHOOT = 1
ACTION_ROTATE_RIGHT = 2
ACTION_ROTATE_LEFT = 3


ACTION_LIST_INFO = [(ACTION_NONE, 'No action'), (ACTION_SHOOT, 'Shoot'), (ACTION_ROTATE_LEFT, 'Rotate Left'), (ACTION_ROTATE_RIGHT, 'Rotate Right')]

_SHAPE_RECTANGLE = 0
_SHAPE_CIRCLE = 1

_POOL_SIZE = 64

# Just their array index in _POSSIBLE_KEYS list
_KEY_INDEX_JUMP = 0
_KEY_INDEX_RIGHT = 1
_KEY_INDEX_LEFT = 2


_POSSIBLE_KEYS = []

#Values associated for keys are designed to be bit fields, so every value is power of 2 and can be mannipulated with binary operators easily
#Tuple is pygame keycode and associated power2 value for bitfield
_POSSIBLE_KEYS.append((pygame.K_SPACE, 0x1))
_POSSIBLE_KEYS.append((pygame.K_RIGHT, 0x2))
_POSSIBLE_KEYS.append((pygame.K_LEFT, 0x4))


#Different ways to destroy an object
_KILLED_NOT = 0
_KILLED_WASTED = 1
_KILLED_BINGO = 2
_KILLED_NEUTRAL = 3



_ROUND_TIME_S = 120
_EXPECTED_FPS = 60
_TIME_PER_CYCLE = 1/_EXPECTED_FPS
_ROUND_CYCLES = _ROUND_TIME_S * _EXPECTED_FPS

_SCREEN_SIZE = [1280, 720]
_OUTPUT_SIZE_FACTOR = 1

#Xmin,XMax - X axis Region of interest of screen in pixels. Depending on this, observation will be bigger or smaller
_REGION_OF_INTEREST = [0,1280]

#Output in X will be reduced according to factor
_OUTPUT_NP_X_LENGHT = (_REGION_OF_INTEREST[1] - _REGION_OF_INTEREST[0]) // _OUTPUT_SIZE_FACTOR

#Mlp will be used and not an image, Y axis is = number of aircraft lanes
_OUTPUT_NP_Y_LENGTH = _SCREEN_SIZE[1]



class GameInstance:
    def __init__(self, caption, mode, render_mode):
        self.Caption = caption
        self.Mode = mode
        self.render_mode = render_mode

        if(not pygame.get_init()):
            pygame.init()
            pygame.display.set_caption(self.Caption)
            self.Screen = pygame.display.set_mode((_SCREEN_SIZE[0], _SCREEN_SIZE[1]))
            self.Clock = pygame.time.Clock()
            self.Font = pygame.font.SysFont(None, 24)
            self.OK = True
        else:
            print('Pygame already running')
            self.OK = False


    def reset(self, seed = 0):

        random.seed(seed)

        if(self.OK):

            # This list is the most important in game, as only instances listed here will be updated and/or rendered. An instance outside this list is unable to do anything
            self.GameObjects = []

            # Declare empty pools
            self.PooledAircrafts = []
            self.PooledParatroopers = []
            self.PooledBullets = []


            # Prepare Pools. This strategy allocates game instances memory, so it will be necessary no more to create instances, just reuse them
            for _ in range(_POOL_SIZE):
                self.PooledAircrafts(_Aircraft())
                self.PooledParatroopers(_Paratrooper())
                self.PooledBullets(_Bullet())

            # Prepare elapsed time
            self.ElapsedTime = 0.0

            #Create output observation array
            self.OutputObs = np.zeros((_OUTPUT_NP_Y_LENGTH, _OUTPUT_NP_X_LENGHT))

            # Running game = True (by the moment)
            self.Running = True

            # Score initialization
            self.Score = 0

            # Neutral pressed keys in bit field is 0
            self.DownKeys = 0x0

            # Launch a first black screen to window
            self.Screen.fill('black')
            pygame.display.flip()

            return self.OutputObs
        else:
            raise Exception("Game cannot start")
        
    # Information
    def isRunning(self):
        return self.Running

    # Basic close operation (terminates game and also pygame system and window)
    def close(self):
        if(self.Running):
            self.Running = False

        if(pygame.get_init()):
            pygame.quit()

    # Get pressed keys and determine an action
    def _KeyDetection(self):
        keys = pygame.key.get_pressed()

        # Neutral pressed keys in bit field is 0
        actualDownKeys = 0x0
        
        # Search along all possible declared keys, the ones which were pressed by doing OR operation, as they are power of 2, they will not overlap
        for i in range(len(_POSSIBLE_KEYS)):
            if keys[_POSSIBLE_KEYS[i][0]]:
                actualDownKeys |= _POSSIBLE_KEYS[i][1]

        # XOR between actual used keys and last cycle will give the keys which suffered a change between this and last cycle
        keyDiff = (self.DownKeys ^ actualDownKeys)

        # Just now pressed keys (action to push, not to maintain pushed), are the ones which suffered a change AND actual down keys
        pressedKeys = keyDiff & actualDownKeys

        # Just now released keys are the ones which suffered a change AND previous active keys
        releasedKeys = keyDiff & self.DownKeys

        # Priorities in determining output action: SHOOT > RIGHT > LEFT
        if(pressedKeys & _POSSIBLE_KEYS[_KEY_INDEX_JUMP][1]):
            outAction = ACTION_SHOOT
        elif(actualDownKeys & _POSSIBLE_KEYS[_KEY_INDEX_RIGHT][1]): # uses actualDownKeys as action can be continuous (no need to press again)
            outAction = ACTION_ROTATE_RIGHT
        elif(actualDownKeys & _POSSIBLE_KEYS[_KEY_INDEX_LEFT][1]): # uses actualDownKeys as action can be continuous (no need to press again)
            outAction = ACTION_ROTATE_LEFT
        else:
            outAction = ACTION_NONE

        # Update downkeys so in next cycle will be possible to observe press/release changes
        self.DownKeys = actualDownKeys

        return outAction

    def _Shoot(self):
        if(self.BulletReady):
            if(len(self.BulletPool)>0):
                newBullet = self.BulletPool.pop(0)
                newBullet.ReCreate(pygame.Vector2(self.Screen.get_width() / 2, self.Screen.get_height() - 32), pygame.Vector2(0, -_DIFFICULTY_BULLET_SPEED))
                self.GameObjects.append(newBullet)
                self.ActiveBullets.append(newBullet)
    
                self.BulletReady = False
                self.ReloadTimeout = _DIFFICULTY_RELOAD_TIME_BULLET
            else:
                print('Critical Error, bullet pool exhausted')
                self.Running = False

    def _ShootReload(self):
        if(self.ReloadTimeout > 0):
            self.ReloadTimeout -= 1
            if(self.ReloadTimeout == 0):
                self.BulletReady = True

  

    # The most important action, as it processes one game step taking note on given external action and giving an observation for this processed step (Gfx render is not done here)
    def step(self, extAction = ACTION_NONE):


        info = {}

        quited = False
        truncated = False

        if(self.Running and (self.render_mode == 'human')):
            # poll for events (this is slow operation, so it is not intended to be done whilst ai training. That will in counterpart freeze game window
            # pygame.QUIT event means the user clicked X to close your window    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.Running = False
                    quited = True
                    break

        if(self.Running):
            #Detect keys if Human is playing, otherwise take external action
            if(self.Mode == GAME_MODE_NORMAL):
                inputAction = self._KeyDetection()
            else:
                inputAction = extAction
        

                
            if(inputAction == ACTION_SHOOT):
                pass

            # Clear virtual output
            self.OutputObs.fill(0.0)
                
            # Every-instance-loop (most important part of step)
            for gObject in self.GameObjects:
                gObject.Update()

                if((gObject.killed == _KILLED_NOT)and(gObject.position.x > _REGION_OF_INTEREST[0])and(gObject.position.x < _REGION_OF_INTEREST[1])):
                    virtualwidth = int(gObject.shapeSize.x /_OUTPUT_SIZE_FACTOR)
                    virtualpos = int((gObject.position.x - _REGION_OF_INTEREST[0]) / _OUTPUT_SIZE_FACTOR)
                            
                    virtualmin = max(0,virtualpos - virtualwidth//2)
                    virtualmax = min(_OUTPUT_NP_X_LENGHT-1, virtualpos + virtualwidth//2) + 1

                    self.OutputObs[gObject.height,virtualmin:virtualmax] = 1.0
        
            
            # Increment elapsed time
            self.ElapsedTime +=_TIME_PER_CYCLE

            # End game when time is over
            if(self.ElapsedTime >= _ROUND_TIME_S):
                self.Running =False
                truncated = True
        


        done = not self.Running and not truncated
         
        info['none'] = 0
        

        if(quited):
            trimmed = True
            self.close()
                
        return self.OutputObs, done, truncated, info

    # Rendering is optional when training AI, but is required in Env wrapper
    def render(self):
        if(self.Running):
            # fill the screen with a color to wipe away anything from last frame
            self.Screen.fill('black')

            # Render objects with their own custom function
            for gObject in self.GameObjects:
                gObject.Draw(self.Screen)

            # Info text
            img = self.Font.render('SCORE: '+str(self.Score), True, 'white')
            self.Screen.blit(img, (10, 10))
            img = self.Font.render('REMAINING TIME: '+str(_ROUND_TIME_S - int(self.ElapsedTime)), True, 'white')
            self.Screen.blit(img, (10, 110))
        
            # flip() the display to put your work on screen
            pygame.display.flip()

            # limits FPS to 60 when playing rendered
            self.Clock.tick(_EXPECTED_FPS)  





