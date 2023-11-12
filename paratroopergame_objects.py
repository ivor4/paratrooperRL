OBJ_TYPE_CANNON = 0
OBJ_TYPE_BULLET = 1
OBJ_TYPE_EXPLOSION = 2


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


class _Cannon(_GameObject):
    def __init__(self, shapeColor, position):
        super().__init__(_SHAPE_RECTANGLE, shapeColor, pygame.Vector2(16,32), OBJ_TYPE_CANNON)
        self.position = position

class _Bullet(_GameObject):
    def __init__(self):
        super().__init__(_SHAPE_CIRCLE, 'red', pygame.Vector2(4,4), OBJ_TYPE_BULLET)
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
        super().__init__(_SHAPE_CIRCLE, 'yellow', pygame.Vector2(2,2), OBJ_TYPE_EXPLOSION)
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