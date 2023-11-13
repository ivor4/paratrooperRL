from paratroopergame_cfg import *
import pygame
import math


class GameObject:

    #Static Variable (same for ALL objects). Game System will pass its value on startup
    GameObjects = None

    def __init__(self, objType):
        self.objType = objType 

    def _reset(self,shapeType, shapeColor, shapeSize):
        self.shapeType = shapeType
        self.shapeColor = shapeColor
        self.shapeSize = shapeSize
        self.position = pygame.Vector2(0, 0)
        self.speed = pygame.Vector2(0, 0)
        self.rect = pygame.Rect(self.position.x, self.position.y, self.shapeSize.x, self.shapeSize.y)
        self.killed = KILLED_NOT
        

    def ReCreate(self, shapeType, shapeColor, shapeSize):
        self._reset(shapeType,shapeColor,shapeSize)
        GameObject.GameObjects.append(self)

    def Destroy(self):
        GameObject.GameObjects.remove(self)
        
    def Update(self):
        self.position.x += self.speed.x
        self.position.y += self.speed.y

        self.rect.width = self.shapeSize.x
        self.rect.height = self.shapeSize.y
        
        self.rect.left = self.position.x - self.rect.width*0.5
        self.rect.top = self.position.y - self.rect.height*0.5

    def Kill(self, reason):
        self.killed = reason 

    def Draw(self, surface):
        if(self.shapeType == SHAPE_CIRCLE):
            pygame.draw.circle(surface, self.shapeColor, self.position, self.shapeSize.x)
        else:
            pygame.draw.rect(surface, self.shapeColor, self.rect)


class Cannon(GameObject):
    def __init__(self):
        super().__init__(OBJ_TYPE_CANNON)
        self.segments = []
        for _ in range(CANNON_SEGMENTS):
            self.segments.append(pygame.Rect(0, 0, CANNON_SEGMENT_SIZE[0], CANNON_SEGMENT_SIZE[1]))

    def ReCreate(self, position):
        super().ReCreate(SHAPE_RECTANGLE, 'white', pygame.Vector2(CANNON_SIZE))

        self.position = position
        self.angle = (CANNON_MAX_ANGLE + CANNON_MIN_ANGLE) / 2.0

        self.segments[0].centerx = position.x
        self.segments[0].centery = position.y

    def MoveRight(self):
        self.angle = max(CANNON_MIN_ANGLE, self.angle - CANNON_ANGLE_ADVANCE)

    def MoveLeft(self):
        self.angle = min(CANNON_MAX_ANGLE, self.angle + CANNON_ANGLE_ADVANCE)

    def Update(self):
        super().Update()

    #Override parent class (don't let it draw standard rectangle), super() won't be called
    def Draw(self, surface):
        pygame.draw.rect(surface, self.shapeColor,self.segments[0])

        for i in range(1,CANNON_SEGMENTS):
            radius = CANNON_SEGMENT_RADIUS*(i)
            self.segments[i].centerx = self.position.x + radius*math.cos(self.angle)
            self.segments[i].centery = self.position.y - radius*math.sin(self.angle)
            pygame.draw.rect(surface, self.shapeColor,self.segments[i])

class Bullet(GameObject):

    #Game system will pass this list value
    ActiveBullets = None

    def __init__(self):
        super().__init__(OBJ_TYPE_BULLET)

    def ReCreate(self, position, initialSpeed):
        super().ReCreate(SHAPE_CIRCLE, 'red', pygame.Vector2(4,4))

        self.WasUseful = False
        self.position = position
        self.speed = initialSpeed

        Bullet.ActiveBullets.append(self)

    def Destroy(self):
        Bullet.ActiveBullets.remove(self)
        super().Destroy()

    def Update(self):
        super().Update()
        if(not SCREEN_RECT.collidepoint(self.position)):
            if(self.WasUseful):
                self.Kill(KILLED_NEUTRAL)
            else:
                self.Kill(KILLED_WASTED)

    def setWasUseful(self):
        self.WasUseful = True


class Explosion(GameObject):
    def __init__(self):
        super().__init__(OBJ_TYPE_EXPLOSION)

    def ReCreate(self, position):
        super().ReCreate(SHAPE_CIRCLE, 'yellow', pygame.Vector2(2,2))

        self.Timeout = 30
        self.position = position

    def Update(self):
        super().Update()
        self.Timeout -= 1
        if(self.Timeout <= 0):
            self.Kill(KILLED_NEUTRAL)
        else:
            radius = (30 - self.Timeout) * 10 / 30
            self.shapeSize = pygame.Vector2(radius,radius)


class Aircraft(GameObject):
    def __init__(self):
        super().__init__(OBJ_TYPE_AIRCRAFT)

    def ReCreate(self, position):
        super().ReCreate(SHAPE_RECTANGLE, 'blue', pygame.Vector2(48,16))

        self.position = position

    def Update(self):
        super().Update()


class Paratrooper(GameObject):
    def __init__(self):
        super().__init__(OBJ_TYPE_PARATROOPER)

    def ReCreate(self, position):
        super().ReCreate(SHAPE_RECTANGLE, 'blue', pygame.Vector2(16,48))

        self.position = position

    def Update(self):
        super().Update()


#Decorative
class Wall(GameObject):
    def __init__(self):
        super().__init__(OBJ_TYPE_WALL)

    def ReCreate(self, position, size):
        super().ReCreate(SHAPE_RECTANGLE, 'gray', size)

        self.position = position