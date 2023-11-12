import pygame
import random
import numpy as np


GAME_MODE_NORMAL = 0
GAME_MODE_EXT_ACTION = 1

ACTION_NONE = 0
ACTION_SHOOT = 1

ACTION_LIST_INFO = [(ACTION_NONE, 'No action'), (ACTION_SHOOT, 'Shoot')]

_SHAPE_RECTANGLE = 0
_SHAPE_CIRCLE = 1



_KEY_INDEX_JUMP = 0

_POSSIBLE_KEYS = []

_POSSIBLE_KEYS.append((pygame.K_SPACE, 0x1))

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

#Xmin,XMax - X axis Region of interest of screen in pixels
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
            self.GameObjects = []

            self.ElapsedTime = 0.0
            self.OutputObs = np.zeros((_OUTPUT_NP_Y_LENGTH, _OUTPUT_NP_X_LENGHT))

            
            self.Running = True
            self.Score = 0
            self.DownKeys = 0x0


            self.Screen.fill('black')
            pygame.display.flip()

            return self.OutputObs
        else:
            raise Exception("Game cannot start")
        

    def isRunning(self):
        return self.Running

    def close(self):
        if(self.Running):
            self.Running = False

        if(pygame.get_init()):
            pygame.quit()

    def _KeyDetection(self):
        keys = pygame.key.get_pressed()

        actualDownKeys = 0x0
        
        for i in range(len(_POSSIBLE_KEYS)):
            if keys[_POSSIBLE_KEYS[i][0]]:
                actualDownKeys |= _POSSIBLE_KEYS[i][1]

        keyDiff = (self.DownKeys ^ actualDownKeys)
        pressedKeys = keyDiff & actualDownKeys
        releasedKeys = keyDiff & self.DownKeys

        if(pressedKeys & _POSSIBLE_KEYS[_KEY_INDEX_JUMP][1]):
            outAction = ACTION_SHOOT
        else:
            outAction = ACTION_NONE

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

  

    def step(self, extAction = ACTION_NONE):
        #obs, dones, info
        info = {}

        quited = False
        trimmed = False

        if(self.Running and (self.render_mode == 'human')):
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.Running = False
                    quited = True
                    break

        if(self.Running):
            # RENDER YOUR GAME HERE
        
            if(self.Mode == GAME_MODE_NORMAL):
                inputAction = self._KeyDetection()
            else:
                inputAction = extAction
        

                
            if(inputAction == ACTION_SHOOT):
                pass

            #Clear virtual output
            self.OutputObs.fill(0.0)
                
            for gObject in self.GameObjects:
                gObject.Update()

                if((gObject.killed == _KILLED_NOT)and(gObject.position.x > _REGION_OF_INTEREST[0])and(gObject.position.x < _REGION_OF_INTEREST[1])):
                    virtualwidth = int(gObject.shapeSize.x /_OUTPUT_SIZE_FACTOR)
                    virtualpos = int((gObject.position.x - _REGION_OF_INTEREST[0]) / _OUTPUT_SIZE_FACTOR)
                            
                    virtualmin = max(0,virtualpos - virtualwidth//2)
                    virtualmax = min(_OUTPUT_NP_X_LENGHT-1, virtualpos + virtualwidth//2) + 1

                    self.OutputObs[gObject.height,virtualmin:virtualmax] = 1.0
        
            

            self.ElapsedTime +=_TIME_PER_CYCLE

            #End game when time is over
            if(self.ElapsedTime >= _ROUND_TIME_S):
                self.Running =False
                trimmed = True
        


        done = not self.Running and not trimmed
         
        info['none'] = 0
        

        if(quited):
            trimmed = True
            self.close()
                
        return self.OutputObs, done, trimmed, info

    def render(self):
        if(self.Running):
            # fill the screen with a color to wipe away anything from last frame
            self.Screen.fill('black')

            # Render objects with their own custom function
            for gObject in self.GameObjects:
                gObject.Draw(self.Screen)

            img = self.Font.render('SCORE: '+str(self.Score), True, 'white')
            self.Screen.blit(img, (10, 10))
            img = self.Font.render('REMAINING TIME: '+str(_ROUND_TIME_S - int(self.ElapsedTime)), True, 'white')
            self.Screen.blit(img, (10, 110))
        
            # flip() the display to put your work on screen
            pygame.display.flip()

            # limits FPS to 60
            self.Clock.tick(_EXPECTED_FPS)  


class _GameObject:
    def __init__(self, shapeType, shapeColor, shapeSize, objType):
        self.objType = objType 

        self.shapeType = shapeType
        self.shapeColor = shapeColor
        self.shapeSize = shapeSize
        self.position = pygame.Vector2(0, 0)
        self.speed = pygame.Vector2(0, 0)
        self.rect = pygame.Rect(self.position.x, self.position.y, self.shapeSize.x, self.shapeSize.y)
        self.killed = _KILLED_NOT

    def ReCreate(self, shapeType, shapeColor, shapeSize):
        self.shapeType = shapeType
        self.shapeColor = shapeColor
        self.shapeSize = shapeSize
        self.position = pygame.Vector2(0, 0)
        self.speed = pygame.Vector2(0, 0)
        self.rect = pygame.Rect(self.position.x, self.position.y, self.shapeSize.x, self.shapeSize.y)
        self.killed = _KILLED_NOT
        
    def Update(self):
        self.position.x += self.speed.x
        self.position.y += self.speed.y

        self.rect.width = self.shapeSize.x
        self.rect.height = self.shapeSize.y
        
        self.rect.left = self.position.x - self.rect.width/2
        self.rect.top = self.position.y - self.rect.height/2

    def Kill(self, reason):
        self.killed = reason 

    def Draw(self, surface):
        if(self.shapeType == _SHAPE_CIRCLE):
            pygame.draw.circle(surface, self.shapeColor, self.position, self.shapeSize.x)
        else:
            pygame.draw.rect(surface, self.shapeColor, self.rect)


class _Canyon(_GameObject):
    def __init__(self, shapeColor, position):
        super().__init__(_SHAPE_RECTANGLE, shapeColor, pygame.Vector2(16,32), _OBJ_TYPE_CANYON)
        self.position = position

class _Bullet(_GameObject):
    def __init__(self):
        super().__init__(_SHAPE_CIRCLE, 'red', pygame.Vector2(4,4), _OBJ_TYPE_BULLET)
        self.WasUseful = False

    def ReCreate(self, position, initialSpeed):
        super().ReCreate(_SHAPE_CIRCLE, 'red', pygame.Vector2(4,4))
        self.WasUseful = False

        self.position = position
        self.speed = initialSpeed

    def Update(self):
        super().Update()
        if(self.position.y < 0):
            if(self.WasUseful):
                self.Kill(_KILLED_NEUTRAL)
            else:
                self.Kill(_KILLED_WASTED)

    def setWasUseful(self):
        self.WasUseful = True


class _Explosion(_GameObject):
    def __init__(self):
        super().__init__(_SHAPE_CIRCLE, 'yellow', pygame.Vector2(2,2), _OBJ_TYPE_EXPLOSION)
        self.Timeout = 0

    def ReCreate(self, position):
        super().ReCreate(_SHAPE_CIRCLE, 'yellow', pygame.Vector2(2,2))

        self.Timeout = 30
        self.position = position

    def Update(self):
        super().Update()
        self.Timeout -= 1
        if(self.Timeout <= 0):
            self.Kill(_KILLED_NEUTRAL)
        else:
            radius = (30 - self.Timeout) * 10 / 30
            self.shapeSize = pygame.Vector2(radius,radius)





