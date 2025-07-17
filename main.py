import pygame
import random
import sys
import math
from enum import Enum
import numpy as np
from pygame import gfxdraw

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Константы
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 960
CELL_SIZE = 20
FPS = 60
UI_HEIGHT = 120
MINIMAP_SIZE = 150
MAP_WIDTH = 100
MAP_HEIGHT = 75

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
CYAN = (0, 255, 255)
YELLOW = (200, 200, 50)
GRAY = (100, 100, 100)
PURPLE = (150, 50, 150)
ORANGE = (200, 150, 50)
DARK_GREEN = (0, 100, 0)
DARK_RED = (100, 0, 0)
LIGHT_BLUE = (100, 100, 255, 100)
DARK_BLUE = (0, 0, 100)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
STONE = (160, 160, 160)
WOOD = (101, 67, 33)

# Звуки
try:
    SELECT_SOUND = pygame.mixer.Sound('select.wav')
    BUILD_SOUND = pygame.mixer.Sound('build.wav')
    ATTACK_SOUND = pygame.mixer.Sound('attack.wav')
    DEATH_SOUND = pygame.mixer.Sound('death.wav')
    VICTORY_SOUND = pygame.mixer.Sound('victory.wav')
    DEFEAT_SOUND = pygame.mixer.Sound('defeat.wav')
    RESOURCE_SOUND = pygame.mixer.Sound('resource.wav')
except:
    # Заглушки если звуки не найдены
    SELECT_SOUND = pygame.mixer.Sound(buffer=bytearray(100))
    BUILD_SOUND = pygame.mixer.Sound(buffer=bytearray(100))
    ATTACK_SOUND = pygame.mixer.Sound(buffer=bytearray(100))
    DEATH_SOUND = pygame.mixer.Sound(buffer=bytearray(100))
    VICTORY_SOUND = pygame.mixer.Sound(buffer=bytearray(100))
    DEFEAT_SOUND = pygame.mixer.Sound(buffer=bytearray(100))
    RESOURCE_SOUND = pygame.mixer.Sound(buffer=bytearray(100))

# Типы юнитов
class UnitType(Enum):
    WARRIOR = 1
    ARCHER = 2
    CAVALRY = 3
    HEALER = 4
    SIEGE = 5
    SCOUT = 6
    WORKER = 7
    MINER = 8
    LUMBERJACK = 9

# Типы зданий
class BuildingType(Enum):
    BARRACKS = 1
    ARCHERY = 2
    STABLE = 3
    TEMPLE = 4
    SIEGE_WORKSHOP = 5
    WALL = 6
    TOWER = 7
    TOWN_HALL = 8
    MINE = 9
    LUMBER_MILL = 10
    FARM = 11

# Типы ресурсов
class ResourceType(Enum):
    GOLD = 1
    STONE = 2
    WOOD = 3
    FOOD = 4

class Game:
    def __init__(self):
        self.grid_width = MAP_WIDTH
        self.grid_height = MAP_HEIGHT
        self.player_units = []
        self.enemy_units = []
        self.player_buildings = []
        self.enemy_buildings = []
        self.resources = []
        self.selected_units = []
        self.selected_building = None
        self.player_resources = {
            'gold': 200,
            'stone': 100,
            'wood': 150,
            'food': 200
        }
        self.enemy_resources = {
            'gold': 200,
            'stone': 100,
            'wood': 150,
            'food': 200
        }
        self.turn = 0
        self.selection_start = None
        self.selection_end = None
        self.game_over = None
        self.game_speed = 1.0
        self.camera_x = 0
        self.camera_y = 0
        self.show_minimap = True
        self.fog_of_war = True
        self.vision_map = np.zeros((self.grid_width, self.grid_height), dtype=bool)
        self.terrain = self.generate_terrain()
        self.particles = []
        self.generate_resources()
        
        # Создаем начальные базы
        self.player_base = self.create_building('player', BuildingType.TOWN_HALL, 10, self.grid_height//2)
        self.player_base['is_base'] = True
        self.player_base['health'] = 500
        self.player_base['max_health'] = 500
        
        self.enemy_base = self.create_building('enemy', BuildingType.TOWN_HALL, self.grid_width-10, self.grid_height//2)
        self.enemy_base['is_base'] = True
        self.enemy_base['health'] = 500
        self.enemy_base['max_health'] = 500
        
        # Создаем начальные юниты
        for _ in range(3):
            self.create_unit('player', UnitType.WARRIOR)
            self.create_unit('player', UnitType.WORKER)
            
        for _ in range(5):
            self.create_unit('enemy', UnitType.WARRIOR)
        for _ in range(2):
            self.create_unit('enemy', UnitType.WORKER)
            
        # Создаем начальные здания
        self.player_buildings.append(self.player_base)
        self.enemy_buildings.append(self.enemy_base)
        
        # Исследованные области
        self.explored = np.zeros((self.grid_width, self.grid_height), dtype=bool)
        
    def generate_terrain(self):
        terrain = np.zeros((self.grid_width, self.grid_height))
        
        # Генерация шума Перлина для рельефа
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                value = 0
                scale = 1.0
                weight = 1.0
                
                for _ in range(4):
                    nx = x / self.grid_width * scale
                    ny = y / self.grid_height * scale
                    value += weight * noise(nx, ny)
                    scale *= 2.0
                    weight *= 0.5
                
                terrain[x, y] = value
        
        # Нормализация
        terrain = (terrain - terrain.min()) / (terrain.max() - terrain.min())
        return terrain
    
    def generate_resources(self):
        # Генерация золота
        for _ in range(15):
            x = random.randint(0, self.grid_width-1)
            y = random.randint(0, self.grid_height-1)
            if self.get_terrain_at(x, y) > 0.4:  # Не в воде
                amount = random.randint(500, 1500)
                self.resources.append({
                    'x': x,
                    'y': y,
                    'type': ResourceType.GOLD,
                    'amount': amount,
                    'color': GOLD
                })
        
        # Генерация камня
        for _ in range(20):
            x = random.randint(0, self.grid_width-1)
            y = random.randint(0, self.grid_height-1)
            if self.get_terrain_at(x, y) > 0.8:  # В горах
                amount = random.randint(300, 1000)
                self.resources.append({
                    'x': x,
                    'y': y,
                    'type': ResourceType.STONE,
                    'amount': amount,
                    'color': STONE
                })
        
        # Генерация дерева
        for _ in range(30):
            x = random.randint(0, self.grid_width-1)
            y = random.randint(0, self.grid_height-1)
            if 0.4 < self.get_terrain_at(x, y) < 0.7:  # В лесу
                amount = random.randint(200, 800)
                self.resources.append({
                    'x': x,
                    'y': y,
                    'type': ResourceType.WOOD,
                    'amount': amount,
                    'color': WOOD
                })
    
    def get_terrain_at(self, x, y):
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            return self.terrain[int(x), int(y)]
        return 0
    
    def get_terrain_multiplier(self, x, y):
        terrain = self.get_terrain_at(x, y)
        if terrain < 0.3:  # Вода
            return 0.3
        elif terrain < 0.4:  # Болото
            return 0.6
        elif terrain > 0.8:  # Горы
            return 0.7
        return 1.0  # Равнина
    
    def get_unit_stats(self, unit_type):
        stats = {
            UnitType.WARRIOR: {
                'health': 25, 'damage': 4, 'speed': 0.6, 'range': 1, 
                'cost': {'gold': 25, 'wood': 10}, 'color': GREEN, 'build_time': 30
            },
            UnitType.ARCHER: {
                'health': 20, 'damage': 3, 'speed': 0.6, 'range': 6, 
                'cost': {'gold': 30, 'wood': 15}, 'color': BLUE, 'build_time': 40
            },
            UnitType.CAVALRY: {
                'health': 35, 'damage': 6, 'speed': 1.2, 'range': 1, 
                'cost': {'gold': 45, 'wood': 20}, 'color': PURPLE, 'build_time': 50
            },
            UnitType.HEALER: {
                'health': 22, 'damage': 0, 'speed': 0.6, 'range': 5, 
                'cost': {'gold': 35, 'wood': 15}, 'color': ORANGE, 'build_time': 45, 
                'heal_amount': 3
            },
            UnitType.SIEGE: {
                'health': 40, 'damage': 10, 'speed': 0.4, 'range': 8, 
                'cost': {'gold': 60, 'wood': 30, 'stone': 20}, 'color': BROWN, 
                'build_time': 70, 'bonus_vs_buildings': 2.0
            },
            UnitType.SCOUT: {
                'health': 15, 'damage': 2, 'speed': 1.5, 'range': 4, 
                'cost': {'gold': 20, 'wood': 5}, 'color': YELLOW, 'build_time': 25, 
                'vision_range': 8
            },
            UnitType.WORKER: {
                'health': 15, 'damage': 1, 'speed': 0.8, 'range': 1, 
                'cost': {'gold': 20, 'food': 10}, 'color': CYAN, 'build_time': 25,
                'gather_rate': {'gold': 1, 'stone': 0.5, 'wood': 1, 'food': 1},
                'build_range': 2,
                'carry_capacity': 20
            },
            UnitType.MINER: {
                'health': 18, 'damage': 1, 'speed': 0.6, 'range': 1, 
                'cost': {'gold': 25, 'food': 10}, 'color': SILVER, 'build_time': 30,
                'gather_rate': {'gold': 2, 'stone': 1, 'wood': 0.2, 'food': 0.2},
                'build_range': 2,
                'carry_capacity': 30
            },
            UnitType.LUMBERJACK: {
                'health': 18, 'damage': 1, 'speed': 0.6, 'range': 1, 
                'cost': {'gold': 25, 'food': 10}, 'color': WOOD, 'build_time': 30,
                'gather_rate': {'gold': 0.2, 'stone': 0.2, 'wood': 2, 'food': 0.5},
                'build_range': 2,
                'carry_capacity': 30
            }
        }
        return stats.get(unit_type)
    
    def get_building_stats(self, building_type):
        stats = {
            BuildingType.BARRACKS: {
                'health': 200, 'cost': {'gold': 100, 'wood': 50}, 'size': 3, 
                'color': DARK_GREEN, 'build_time': 100, 'produces': UnitType.WARRIOR
            },
            BuildingType.ARCHERY: {
                'health': 180, 'cost': {'gold': 120, 'wood': 80}, 'size': 3, 
                'color': DARK_BLUE, 'build_time': 120, 'produces': UnitType.ARCHER
            },
            BuildingType.STABLE: {
                'health': 220, 'cost': {'gold': 150, 'wood': 100}, 'size': 3, 
                'color': PURPLE, 'build_time': 140, 'produces': UnitType.CAVALRY
            },
            BuildingType.TEMPLE: {
                'health': 180, 'cost': {'gold': 130, 'wood': 60}, 'size': 3, 
                'color': ORANGE, 'build_time': 130, 'produces': UnitType.HEALER
            },
            BuildingType.SIEGE_WORKSHOP: {
                'health': 200, 'cost': {'gold': 160, 'wood': 100, 'stone': 50}, 'size': 4, 
                'color': BROWN, 'build_time': 150, 'produces': UnitType.SIEGE
            },
            BuildingType.WALL: {
                'health': 250, 'cost': {'gold': 50, 'stone': 30}, 'size': 1, 
                'color': GRAY, 'build_time': 60
            },
            BuildingType.TOWER: {
                'health': 180, 'cost': {'gold': 80, 'stone': 50}, 'size': 2, 
                'color': DARK_RED, 'build_time': 90, 'damage': 5, 'range': 7
            },
            BuildingType.TOWN_HALL: {
                'health': 500, 'cost': {'gold': 200, 'wood': 150, 'stone': 100}, 'size': 4, 
                'color': CYAN, 'build_time': 200, 'produces': UnitType.WORKER,
                'income': {'gold': 5, 'food': 3}
            },
            BuildingType.MINE: {
                'health': 150, 'cost': {'gold': 100, 'wood': 50, 'stone': 30}, 'size': 3, 
                'color': SILVER, 'build_time': 120, 'produces': UnitType.MINER,
                'income': {'gold': 2, 'stone': 1}
            },
            BuildingType.LUMBER_MILL: {
                'health': 150, 'cost': {'gold': 100, 'wood': 80}, 'size': 3, 
                'color': WOOD, 'build_time': 120, 'produces': UnitType.LUMBERJACK,
                'income': {'wood': 3}
            },
            BuildingType.FARM: {
                'health': 120, 'cost': {'gold': 80, 'wood': 40}, 'size': 3, 
                'color': GREEN, 'build_time': 90, 'income': {'food': 5}
            }
        }
        return stats.get(building_type)
    
    def can_afford(self, side, cost_dict):
        resources = self.player_resources if side == 'player' else self.enemy_resources
        for resource, amount in cost_dict.items():
            if resources.get(resource, 0) < amount:
                return False
        return True
    
    def spend_resources(self, side, cost_dict):
        resources = self.player_resources if side == 'player' else self.enemy_resources
        for resource, amount in cost_dict.items():
            resources[resource] -= amount
    
    def create_unit(self, side, unit_type, x=None, y=None):
        stats = self.get_unit_stats(unit_type)
        if not stats or not self.can_afford(side, stats['cost']):
            return False
            
        if side == 'player':
            if x is None or y is None:
                # Ищем свободное место вокруг базы
                base = self.player_base
                for attempt in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(2, 4)
                    x = base['x'] + math.cos(angle) * distance
                    y = base['y'] + math.sin(angle) * distance
                    
                    # Проверяем, что место свободно
                    if (0 <= x < self.grid_width and 0 <= y < self.grid_height and
                        not self.is_position_blocked(x, y)):
                        break
            
            unit = {
                'x': x, 
                'y': y,
                'health': stats['health'],
                'max_health': stats['health'],
                'damage': stats['damage'],
                'speed': stats['speed'] * self.game_speed,
                'range': stats['range'],
                'type': unit_type,
                'color': stats['color'],
                'target_x': None,
                'target_y': None,
                'attacking': False,
                'cooldown': 0,
                'build_progress': 0,
                'build_time': stats.get('build_time', 0),
                'side': side,
                'heal_amount': stats.get('heal_amount', 0),
                'bonus_vs_buildings': stats.get('bonus_vs_buildings', 1.0),
                'vision_range': stats.get('vision_range', 5),
                'building': True if stats.get('build_time', 0) > 0 else False,
                'gathering': False,
                'gather_target': None,
                'gather_rate': stats.get('gather_rate', {}),
                'carrying': {'gold': 0, 'stone': 0, 'wood': 0, 'food': 0},
                'build_range': stats.get('build_range', 0),
                'carry_capacity': stats.get('carry_capacity', 20),
                'path': []
            }
            
            self.player_units.append(unit)
            if unit['build_time'] <= 0:
                BUILD_SOUND.play()
            self.spend_resources('player', stats['cost'])
            return unit
            
        elif side == 'enemy':
            if x is None or y is None:
                base = self.enemy_base
                for attempt in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(2, 4)
                    x = base['x'] + math.cos(angle) * distance
                    y = base['y'] + math.sin(angle) * distance
                    
                    if (0 <= x < self.grid_width and 0 <= y < self.grid_height and
                        not self.is_position_blocked(x, y)):
                        break
            
            unit = {
                'x': x, 
                'y': y, 
                'health': stats['health'],
                'max_health': stats['health'],
                'damage': stats['damage'],
                'speed': stats['speed'] * self.game_speed,
                'range': stats['range'],
                'type': unit_type,
                'color': YELLOW,
                'target_x': None,
                'target_y': None,
                'attacking': False,
                'cooldown': 0,
                'build_progress': 0,
                'build_time': stats.get('build_time', 0),
                'side': side,
                'heal_amount': stats.get('heal_amount', 0),
                'bonus_vs_buildings': stats.get('bonus_vs_buildings', 1.0),
                'vision_range': stats.get('vision_range', 5),
                'building': True if stats.get('build_time', 0) > 0 else False,
                'gathering': False,
                'gather_target': None,
                'gather_rate': stats.get('gather_rate', {}),
                'carrying': {'gold': 0, 'stone': 0, 'wood': 0, 'food': 0},
                'build_range': stats.get('build_range', 0),
                'carry_capacity': stats.get('carry_capacity', 20),
                'path': []
            }
            
            self.enemy_units.append(unit)
            self.spend_resources('enemy', stats['cost'])
            return unit
            
        return False
    
    def is_position_blocked(self, x, y, ignore_unit=None):
        # Проверяем здания
        for building in self.player_buildings + self.enemy_buildings:
            if building['build_progress'] >= building['build_time']:
                dist = self.get_distance(x, y, building['x'], building['y'])
                if dist < building['size'] / 2 + 0.5:
                    return True
        
        # Проверяем юнитов
        for unit in self.player_units + self.enemy_units:
            if unit != ignore_unit and unit['build_progress'] >= unit['build_time']:
                dist = self.get_distance(x, y, unit['x'], unit['y'])
                if dist < 0.7:
                    return True
        
        # Проверяем границы карты
        if x < 0 or x >= self.grid_width or y < 0 or y >= self.grid_height:
            return True
            
        return False
    
    def create_building(self, side, building_type, x, y):
        stats = self.get_building_stats(building_type)
        if not stats or not self.can_afford(side, stats['cost']):
            return False
            
        # Проверяем, что место свободно
        for building in self.player_buildings + self.enemy_buildings:
            if self.get_distance(x, y, building['x'], building['y']) < max(stats['size'], building['size']) + 2:
                return False
        
        if (x - stats['size']/2 < 0 or x + stats['size']/2 >= self.grid_width or
            y - stats['size']/2 < 0 or y + stats['size']/2 >= self.grid_height):
            return False
            
        building = {
            'x': x,
            'y': y,
            'health': stats['health'],
            'max_health': stats['health'],
            'size': stats['size'],
            'type': building_type,
            'color': stats['color'],
            'build_progress': 0,
            'build_time': stats['build_time'],
            'side': side,
            'produces': stats.get('produces'),
            'cooldown': 0,
            'damage': stats.get('damage', 0),
            'range': stats.get('range', 0),
            'income': stats.get('income', {})
        }
        
        if side == 'player':
            self.player_buildings.append(building)
        else:
            self.enemy_buildings.append(building)
            
        self.spend_resources(side, stats['cost'])
        return building
    
    def update_vision(self):
        self.vision_map.fill(False)
        
        for building in self.player_buildings:
            if building['build_progress'] >= building['build_time']:
                vision_range = 6
                self.update_vision_at(building['x'], building['y'], vision_range)
        
        for unit in self.player_units:
            if unit['build_progress'] >= unit['build_time']:
                self.update_vision_at(unit['x'], unit['y'], unit['vision_range'])
        
        base_vision = 10
        self.update_vision_at(self.player_base['x'], self.player_base['y'], base_vision)

    def update_vision_at(self, x, y, radius):
        for dx in range(-radius, radius+1):
            for dy in range(-radius, radius+1):
                nx = int(max(0, min(self.grid_width-1, x + dx)))
                ny = int(max(0, min(self.grid_height-1, y + dy)))
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    self.vision_map[nx, ny] = True
                    self.explored[nx, ny] = True
    
    def update(self):
        if self.game_over:
            return
            
        if self.fog_of_war:
            self.update_vision()
        
        self.update_construction()
        self.move_units()
        self.gather_resources()
        self.fight()
        self.heal_units()
        self.update_buildings()
        self.update_particles()
        
        # Пассивный доход от зданий
        if self.turn % 10 == 0:
            for building in self.player_buildings:
                if building['build_progress'] >= building['build_time']:
                    for resource, amount in building.get('income', {}).items():
                        self.player_resources[resource] += amount
            
            for building in self.enemy_buildings:
                if building['build_progress'] >= building['build_time']:
                    for resource, amount in building.get('income', {}).items():
                        self.enemy_resources[resource] += amount
        
        # ИИ противника
        if self.turn % 30 == 0:
            self.enemy_ai()
        
        self.turn += 1
        
        # Проверка победы/поражения
        if self.player_base['health'] <= 0:
            self.game_over = "Поражение! Ваша база уничтожена."
            DEFEAT_SOUND.play()
        elif self.enemy_base['health'] <= 0:
            self.game_over = "Победа! База врага уничтожена."
            VICTORY_SOUND.play()
    
    def update_construction(self):
        for unit in self.player_units[:] + self.enemy_units[:]:
            if unit.get('building', False):
                unit['build_progress'] += 1
                if unit['build_progress'] >= unit['build_time']:
                    unit['building'] = False
                    if unit['side'] == 'player':
                        BUILD_SOUND.play()
        
        for building in self.player_buildings + self.enemy_buildings:
            if building['build_progress'] < building['build_time']:
                building['build_progress'] += 1
    
    def gather_resources(self):
        for unit in [u for u in self.player_units + self.enemy_units if u.get('gather_rate')]:
            if unit['build_progress'] < unit['build_time']:
                continue
                
            if unit['gathering'] and unit['gather_target']:
                resource = unit['gather_target']
                
                # Проверяем, существует ли еще ресурс
                if resource not in self.resources:
                    unit['gathering'] = False
                    unit['gather_target'] = None
                    continue
                    
                distance = self.get_distance(unit['x'], unit['y'], resource['x'], resource['y'])
                
                if distance > 1.5:  # Подходим к ресурсу
                    # Если нет пути или цель изменилась - пересчитываем путь
                    if (not unit['path'] or 
                        unit['target_x'] != resource['x'] or 
                        unit['target_y'] != resource['y']):
                        unit['target_x'] = resource['x']
                        unit['target_y'] = resource['y']
                        unit['attacking'] = False
                        unit['path'] = self.find_path(unit['x'], unit['y'], resource['x'], resource['y'], unit)
                else:
                    # Собираем ресурс
                    if unit['cooldown'] <= 0:
                        gather_rate = unit['gather_rate']
                        gathered = False
                        
                        for res_type, rate in gather_rate.items():
                            if resource['type'].name.lower() == res_type and resource['amount'] > 0:
                                can_carry = unit['carry_capacity'] - sum(unit['carrying'].values())
                                gather_amount = min(rate, resource['amount'], can_carry)
                                
                                if gather_amount > 0:
                                    unit['carrying'][res_type] += gather_amount
                                    resource['amount'] -= gather_amount
                                    gathered = True
                                    
                                    self.add_particles(resource['x'], resource['y'], 2, resource['color'])
                                    
                                    if resource['amount'] <= 0:
                                        if resource in self.resources:
                                            self.resources.remove(resource)
                                        unit['gather_target'] = None
                                        unit['gathering'] = False
                                        break
                        
                        if gathered:
                            unit['cooldown'] = 20
                            RESOURCE_SOUND.play()
                    else:
                        unit['cooldown'] -= 1
            else:
                # Возвращаем ресурсы на базу, если есть что нести
                if sum(unit['carrying'].values()) > 0:
                    base = self.player_base if unit['side'] == 'player' else self.enemy_base
                    distance = self.get_distance(unit['x'], unit['y'], base['x'], base['y'])
                    
                    if distance > 2:  # Идем к базе
                        if (not unit['path'] or 
                            unit['target_x'] != base['x'] or 
                            unit['target_y'] != base['y']):
                            unit['target_x'] = base['x']
                            unit['target_y'] = base['y']
                            unit['attacking'] = False
                            unit['path'] = self.find_path(unit['x'], unit['y'], base['x'], base['y'], unit)
                    else:
                        # Сдаем ресурсы
                        resources = self.player_resources if unit['side'] == 'player' else self.enemy_resources
                        for res_type, amount in unit['carrying'].items():
                            resources[res_type] += amount
                        
                        unit['carrying'] = {'gold': 0, 'stone': 0, 'wood': 0, 'food': 0}
                        RESOURCE_SOUND.play()
                        
                        # После сдачи ресурсов пытаемся вернуться к сбору, если была цель
                        if unit['gather_target'] and unit['gather_target'] in self.resources:
                            unit['path'] = self.find_path(unit['x'], unit['y'], 
                                                        unit['gather_target']['x'], 
                                                        unit['gather_target']['y'], unit)
    
    def find_path(self, start_x, start_y, target_x, target_y, unit):
        """Упрощенный алгоритм поиска пути"""
        path = []
        
        # Простой алгоритм - двигаемся по прямой, обходя препятствия
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return []
        
        # Нормализуем направление
        dx /= distance
        dy /= distance
        
        # Пытаемся двигаться по прямой
        steps = int(distance * 2)
        last_valid = (start_x, start_y)
        
        for i in range(1, steps + 1):
            x = start_x + dx * i * 0.5
            y = start_y + dy * i * 0.5
            
            if not self.is_position_blocked(x, y, unit):
                last_valid = (x, y)
            else:
                # Если встретили препятствие, пытаемся обойти
                for angle in [math.pi/4, -math.pi/4, math.pi/2, -math.pi/2]:
                    nx = last_valid[0] + math.cos(angle) * 0.5
                    ny = last_valid[1] + math.sin(angle) * 0.5
                    
                    if not self.is_position_blocked(nx, ny, unit):
                        path.append((nx, ny))
                        last_valid = (nx, ny)
                        break
        
        if last_valid != (target_x, target_y):
            path.append((target_x, target_y))
        
        return path
    
    def update_buildings(self):
        for building in self.player_buildings + self.enemy_buildings:
            if (building['build_progress'] >= building['build_time'] and 
                building.get('produces') and 
                building['cooldown'] <= 0):
                
                side = building['side']
                unit_type = building['produces']
                stats = self.get_unit_stats(unit_type)
                
                if self.can_afford(side, stats['cost']):
                    # Ищем свободное место вокруг здания
                    for attempt in range(10):
                        angle = random.uniform(0, 2 * math.pi)
                        distance = random.uniform(2, building['size'] + 2)
                        x = building['x'] + math.cos(angle) * distance
                        y = building['y'] + math.sin(angle) * distance
                        
                        if (0 <= x < self.grid_width and 0 <= y < self.grid_height and
                            not self.is_position_blocked(x, y)):
                            break
                    
                    if side == 'player':
                        self.create_unit('player', unit_type, x, y)
                    else:
                        unit = self.create_unit('enemy', unit_type, x, y)
                        if unit and not unit.get('building', False):
                            self.enemy_units.append(unit)
                    
                    building['cooldown'] = 100
                else:
                    building['cooldown'] -= 1
            else:
                building['cooldown'] -= 1
        
        for building in self.player_buildings + self.enemy_buildings:
            if building['build_progress'] >= building['build_time'] and building.get('damage', 0) > 0:
                if building['cooldown'] <= 0:
                    if building['side'] == 'player':
                        target = self.find_nearest_enemy(building['x'], building['y'])
                    else:
                        target = self.find_nearest_player(building['x'], building['y'])
                    
                    if target and self.get_distance(building['x'], building['y'], target['x'], target['y']) <= building['range']:
                        if isinstance(target, dict):
                            target['health'] -= building['damage']
                        else:
                            target['health'] -= building['damage'] * 0.5
                        
                        self.add_particles(target['x'], target['y'], 5, RED)
                        ATTACK_SOUND.play()
                        building['cooldown'] = 30
                else:
                    building['cooldown'] -= 1
    
    def update_particles(self):
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def add_particles(self, x, y, count, color):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.1, 0.5)
            self.particles.append({
                'x': x,
                'y': y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'life': random.randint(10, 30),
                'color': color,
                'size': random.randint(1, 3)
            })
    
    def enemy_ai(self):
        # Увеличиваем ресурсы врага
        if self.turn % 5 == 0:
            for resource in self.enemy_resources:
                self.enemy_resources[resource] += 5
        
        # Запускаем ИИ каждые 10 ходов
        if self.turn % 10 != 0:
            return
        
        # 1. Строим здания, если их мало
        if len(self.enemy_buildings) < 5 + self.turn // 100:
            building_choices = []
            
            if len([u for u in self.enemy_units if u['type'] == UnitType.WARRIOR]) < 5:
                building_choices.append(BuildingType.BARRACKS)
            if len([u for u in self.enemy_units if u['type'] == UnitType.ARCHER]) < 3:
                building_choices.append(BuildingType.ARCHERY)
            if len([u for u in self.enemy_units if u['type'] == UnitType.CAVALRY]) < 2:
                building_choices.append(BuildingType.STABLE)
            
            if not building_choices:
                building_choices = [BuildingType.BARRACKS, BuildingType.ARCHERY, BuildingType.STABLE, BuildingType.FARM]
            
            building_type = random.choice(building_choices)
            
            x = self.enemy_base['x'] + random.randint(-8, 8)
            y = self.enemy_base['y'] + random.randint(-8, 8)
            
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                self.create_building('enemy', building_type, x, y)
        
        # 2. Производим юнитов из всех доступных зданий
        for building in self.enemy_buildings:
            if (building['build_progress'] >= building['build_time'] and 
                building.get('produces') and 
                building['cooldown'] <= 0):
                
                unit_type = building['produces']
                stats = self.get_unit_stats(unit_type)
                
                if self.can_afford('enemy', stats['cost']):
                    x = building['x'] + random.randint(-2, 2)
                    y = building['y'] + random.randint(-2, 2)
                    unit = self.create_unit('enemy', unit_type, x, y)
                    if unit and not unit.get('building', False):
                        self.enemy_units.append(unit)
        
        # 3. Отправляем юнитов в атаку или на сбор ресурсов
        for unit in self.enemy_units:
            if unit['build_progress'] < unit['build_time']:
                continue
                
            if random.random() < 0.2:  # 20% шанс начать сбор ресурсов
                if unit.get('gather_rate') and not unit['gathering'] and sum(unit['carrying'].values()) < unit.get('carry_capacity', 20):
                    nearest_resource = None
                    min_dist = float('inf')
                    
                    for resource in self.resources:
                        dist = self.get_distance(unit['x'], unit['y'], resource['x'], resource['y'])
                        if dist < min_dist:
                            for res_type in unit['gather_rate']:
                                if resource['type'].name.lower() == res_type:
                                    nearest_resource = resource
                                    min_dist = dist
                                    break
                    
                    if nearest_resource:
                        unit['gather_target'] = nearest_resource
                        unit['gathering'] = True
                        unit['attacking'] = False
            elif len(self.enemy_units) > 3 and random.random() < 0.7:  # 70% шанс начать атаку
                unit['target_x'] = self.player_base['x']
                unit['target_y'] = self.player_base['y']
                unit['attacking'] = True
                unit['path'] = self.find_path(unit['x'], unit['y'], unit['target_x'], unit['target_y'], unit)
    
    def get_distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def move_units(self):
        for unit in self.player_units + self.enemy_units:
            if unit['build_progress'] < unit['build_time']:
                continue
                
            if unit['cooldown'] > 0:
                unit['cooldown'] -= 1
                continue
                
            # Если есть путь - следуем по нему
            if unit['path']:
                next_point = unit['path'][0]
                dx = next_point[0] - unit['x']
                dy = next_point[1] - unit['y']
                distance = self.get_distance(unit['x'], unit['y'], next_point[0], next_point[1])
                
                if distance < 0.3:
                    unit['path'].pop(0)
                else:
                    speed = unit['speed'] * self.get_terrain_multiplier(unit['x'], unit['y'])
                    dx = dx / distance * speed
                    dy = dy / distance * speed
                    
                    new_x = unit['x'] + dx
                    new_y = unit['y'] + dy
                    
                    if not self.is_position_blocked(new_x, new_y, unit):
                        unit['x'] = max(0, min(self.grid_width-1, new_x))
                        unit['y'] = max(0, min(self.grid_height-1, new_y))
                    else:
                        # Если путь заблокирован, пробуем обойти
                        unit['path'] = self.find_path(unit['x'], unit['y'], next_point[0], next_point[1], unit)
                        if not unit['path'] and unit['target_x'] is not None:
                            # Если не получается обойти, ищем новый путь к конечной точке
                            unit['path'] = self.find_path(unit['x'], unit['y'], unit['target_x'], unit['target_y'], unit)
            
            # Если пути нет, но есть целевая точка - идем к ней
            elif unit['target_x'] is not None and unit['target_y'] is not None:
                distance = self.get_distance(unit['x'], unit['y'], unit['target_x'], unit['target_y'])
                
                if distance > 0.5:
                    # Если далеко - ищем путь
                    unit['path'] = self.find_path(unit['x'], unit['y'], unit['target_x'], unit['target_y'], unit)
                    if not unit['path']:
                        # Если путь не найден, пробуем подойти ближе напрямую
                        speed = unit['speed'] * self.get_terrain_multiplier(unit['x'], unit['y'])
                        dx = (unit['target_x'] - unit['x']) / distance * speed
                        dy = (unit['target_y'] - unit['y']) / distance * speed
                        
                        new_x = unit['x'] + dx
                        new_y = unit['y'] + dy
                        
                        if not self.is_position_blocked(new_x, new_y, unit):
                            unit['x'] = max(0, min(self.grid_width-1, new_x))
                            unit['y'] = max(0, min(self.grid_height-1, new_y))
                else:
                    # Достигли цели
                    unit['target_x'] = None
                    unit['target_y'] = None
                    unit['path'] = []
    
    def fight(self):
        for e_unit in self.enemy_units[:]:
            if e_unit['build_progress'] < e_unit['build_time']:
                continue
                
            if e_unit['health'] <= 0:
                self.enemy_units.remove(e_unit)
                self.add_particles(e_unit['x'], e_unit['y'], 15, RED)
                DEATH_SOUND.play()
                continue
                
            if e_unit['cooldown'] > 0:
                continue
                
            target = self.find_nearest_player(e_unit['x'], e_unit['y'])
            if target:
                distance = self.get_distance(e_unit['x'], e_unit['y'], target['x'], target['y'])
                if distance <= e_unit['range']:
                    damage = e_unit['damage']
                    
                    if isinstance(target, dict):
                        if target.get('type') == UnitType.CAVALRY and e_unit.get('type') == UnitType.WARRIOR:
                            damage *= 1.5
                        target['health'] -= damage
                    else:
                        target['health'] -= damage * 0.5
                    
                    e_unit['cooldown'] = 25
                    self.add_particles(target['x'], target['y'], 5, RED)
                    ATTACK_SOUND.play()
        
        for p_unit in self.player_units[:]:
            if p_unit['build_progress'] < p_unit['build_time']:
                continue
                
            if p_unit['health'] <= 0:
                self.player_units.remove(p_unit)
                self.add_particles(p_unit['x'], p_unit['y'], 15, RED)
                DEATH_SOUND.play()
                continue
                
            if p_unit['cooldown'] > 0:
                continue
                
            if p_unit['attacking']:
                target = self.find_nearest_enemy(p_unit['x'], p_unit['y'])
                if target:
                    distance = self.get_distance(p_unit['x'], p_unit['y'], target['x'], target['y'])
                    if distance <= p_unit['range']:
                        damage = p_unit['damage']
                        
                        if isinstance(target, dict):
                            if target.get('type') == UnitType.CAVALRY and p_unit.get('type') == UnitType.WARRIOR:
                                damage *= 1.5
                            elif target.get('type') == UnitType.ARCHER and p_unit.get('type') == UnitType.SCOUT:
                                damage *= 1.3
                            
                            target['health'] -= damage
                        else:
                            damage *= p_unit.get('bonus_vs_buildings', 1.0)
                            target['health'] -= damage
                        
                        p_unit['cooldown'] = 25
                        self.add_particles(target['x'], target['y'], 5, RED)
                        ATTACK_SOUND.play()
    
    def heal_units(self):
        for healer in [u for u in self.player_units if u['type'] == UnitType.HEALER]:
            if healer['build_progress'] < healer['build_time']:
                continue
                
            if healer['cooldown'] > 0:
                continue
                
            healed = False
            for unit in self.player_units + self.player_buildings:
                if unit != healer and unit['health'] < unit['max_health']:
                    distance = self.get_distance(healer['x'], healer['y'], unit['x'], unit['y'])
                    if distance <= healer['range']:
                        heal_amount = healer['heal_amount']
                        
                        if distance > healer['range'] / 2:
                            heal_amount *= 0.7
                        
                        unit['health'] = min(unit['max_health'], unit['health'] + heal_amount)
                        self.add_particles(unit['x'], unit['y'], 3, GREEN)
                        healed = True
            
            if healed:
                healer['cooldown'] = 30
    
    def find_nearest_enemy(self, x, y):
        closest = None
        min_dist = float('inf')
        
        for unit in self.enemy_units:
            if unit['build_progress'] >= unit['build_time']:
                dist = self.get_distance(x, y, unit['x'], unit['y'])
                if dist < min_dist:
                    min_dist = dist
                    closest = unit
        
        for building in self.enemy_buildings:
            if building['build_progress'] >= building['build_time']:
                dist = self.get_distance(x, y, building['x'], building['y'])
                if dist < min_dist:
                    min_dist = dist
                    closest = building
        
        base_dist = self.get_distance(x, y, self.enemy_base['x'], self.enemy_base['y'])
        if base_dist < min_dist:
            return self.enemy_base
        
        return closest
    
    def find_nearest_player(self, x, y):
        closest = None
        min_dist = float('inf')
        
        for unit in self.player_units:
            if unit['build_progress'] >= unit['build_time']:
                dist = self.get_distance(x, y, unit['x'], unit['y'])
                if dist < min_dist:
                    min_dist = dist
                    closest = unit
        
        for building in self.player_buildings:
            if building['build_progress'] >= building['build_time']:
                dist = self.get_distance(x, y, building['x'], building['y'])
                if dist < min_dist:
                    min_dist = dist
                    closest = building
        
        base_dist = self.get_distance(x, y, self.player_base['x'], self.player_base['y'])
        if base_dist < min_dist:
            return self.player_base
        
        return closest
    
    def find_nearest_resource(self, x, y, resource_type=None):
        closest = None
        min_dist = float('inf')
        
        for resource in self.resources:
            if resource_type is None or resource['type'] == resource_type:
                dist = self.get_distance(x, y, resource['x'], resource['y'])
                if dist < min_dist:
                    min_dist = dist
                    closest = resource
        
        return closest
    
    def select_units(self, start_pos, end_pos):
        self.selected_units = []
        self.selected_building = None
        
        # Учитываем смещение камеры и интерфейса
        x1 = (start_pos[0] + self.camera_x // CELL_SIZE)
        y1 = (start_pos[1] + (self.camera_y + UI_HEIGHT) // CELL_SIZE)
        x2 = (end_pos[0] + self.camera_x // CELL_SIZE)
        y2 = (end_pos[1] + (self.camera_y + UI_HEIGHT) // CELL_SIZE)
        
        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        
        for unit in self.player_units:
            if not unit.get('building', False):
                if (left <= unit['x'] <= right and 
                    top <= unit['y'] <= bottom):
                    self.selected_units.append(unit)
        
        if not self.selected_units:
            for building in self.player_buildings:
                if building['build_progress'] >= building['build_time']:
                    building_left = building['x'] - building['size']/2
                    building_right = building['x'] + building['size']/2
                    building_top = building['y'] - building['size']/2
                    building_bottom = building['y'] + building['size']/2
                    
                    if (right > building_left and left < building_right and
                        bottom > building_top and top < building_bottom):
                        self.selected_building = building
                        break
        
        if self.selected_units or self.selected_building:
            SELECT_SOUND.play()
    
    def command_units(self, target_pos):
        if not self.selected_units and not self.selected_building:
            return
            
        x, y = target_pos
        
        # Если выбрано здание с производством
        if self.selected_building and self.selected_building.get('produces'):
            unit_type = self.selected_building['produces']
            stats = self.get_unit_stats(unit_type)
            
            if self.can_afford('player', stats['cost']):
                new_unit = self.create_unit('player', unit_type, 
                                        self.selected_building['x'], 
                                        self.selected_building['y'])
                if new_unit:
                    self.selected_units = [new_unit]
        
        valid_units = [u for u in self.selected_units if not u.get('building', False)]
        if not valid_units:
            return
        
        # 1. Проверяем, не ресурс ли это
        target_resource = None
        for resource in self.resources:
            if self.get_distance(resource['x'], resource['y'], x, y) < 1.5:
                target_resource = resource
                break
        
        if target_resource:
            for unit in valid_units:
                if unit.get('gather_rate'):
                    unit['gather_target'] = target_resource
                    unit['gathering'] = True
                    unit['attacking'] = False
                    unit['target_x'] = target_resource['x']
                    unit['target_y'] = target_resource['y']
                    unit['path'] = self.find_path(unit['x'], unit['y'], 
                                                target_resource['x'], 
                                                target_resource['y'], unit)
            return
        
        # 2. Проверяем, не враг ли это
        target_enemy = None
        for enemy in self.enemy_units + self.enemy_buildings:
            if self.get_distance(enemy['x'], enemy['y'], x, y) < 2.0:
                target_enemy = enemy
                break
        
        if not target_enemy and self.get_distance(self.enemy_base['x'], self.enemy_base['y'], x, y) < 3.0:
            target_enemy = self.enemy_base
        
        if target_enemy:
            for unit in valid_units:
                unit['target_x'] = target_enemy['x']
                unit['target_y'] = target_enemy['y']
                unit['attacking'] = True
                unit['gathering'] = False
                unit['gather_target'] = None
                unit['path'] = self.find_path(unit['x'], unit['y'], 
                                            target_enemy['x'], 
                                            target_enemy['y'], unit)
            return
        
        # 3. Если это точка на карте - двигаемся туда
        center_x = sum(u['x'] for u in valid_units) / len(valid_units)
        center_y = sum(u['y'] for u in valid_units) / len(valid_units)
        
        for i, unit in enumerate(valid_units):
            angle = 2 * math.pi * i / len(valid_units)
            offset_x = math.cos(angle) * 2
            offset_y = math.sin(angle) * 2
            
            unit['target_x'] = x + offset_x
            unit['target_y'] = y + offset_y
            unit['attacking'] = False
            unit['gathering'] = False
            unit['gather_target'] = None
            unit['path'] = self.find_path(unit['x'], unit['y'], 
                                        unit['target_x'], 
                                        unit['target_y'], unit)

    
    def build(self, building_type, x, y):
        stats = self.get_building_stats(building_type)
        if not stats or not self.can_afford('player', stats['cost']):
            return False
        
        for building in self.player_buildings + self.enemy_buildings:
            if self.get_distance(x, y, building['x'], building['y']) < max(stats['size'], building['size']) + 2:
                return False
        
        if (x - stats['size']/2 < 0 or x + stats['size']/2 >= self.grid_width or
            y - stats['size']/2 < 0 or y + stats['size']/2 >= self.grid_height):
            return False
        
        self.create_building('player', building_type, x, y)
        BUILD_SOUND.play()
        return True

def noise(x, y):
    n = math.sin(x * 10 + y * 5) + math.sin(x * 5 + y * 10) * 0.5
    return n / 1.5

def draw_rounded_rect(surface, color, rect, radius=5):
    x, y, w, h = rect
    pygame.gfxdraw.aacircle(surface, x + radius, y + radius, radius, color)
    pygame.gfxdraw.aacircle(surface, x + w - radius, y + radius, radius, color)
    pygame.gfxdraw.aacircle(surface, x + w - radius, y + h - radius, radius, color)
    pygame.gfxdraw.aacircle(surface, x + radius, y + h - radius, radius, color)
    
    pygame.gfxdraw.filled_circle(surface, x + radius, y + radius, radius, color)
    pygame.gfxdraw.filled_circle(surface, x + w - radius, y + radius, radius, color)
    pygame.gfxdraw.filled_circle(surface, x + w - radius, y + h - radius, radius, color)
    pygame.gfxdraw.filled_circle(surface, x + radius, y + h - radius, radius, color)
    
    pygame.draw.rect(surface, color, (x + radius, y, w - 2*radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2*radius))

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Epic Strategy Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 18)
    small_font = pygame.font.SysFont('Arial', 14)
    big_font = pygame.font.SysFont('Arial', 48)
    
    game = Game()
    running = True
    selecting = False
    building_mode = None
    show_help = False
    
    buttons = [
        {"rect": pygame.Rect(10, SCREEN_HEIGHT-110, 120, 30), "text": "Воин (25g,10w)", "type": UnitType.WARRIOR, "building": BuildingType.BARRACKS},
        {"rect": pygame.Rect(140, SCREEN_HEIGHT-110, 120, 30), "text": "Лучник (30g,15w)", "type": UnitType.ARCHER, "building": BuildingType.ARCHERY},
        {"rect": pygame.Rect(270, SCREEN_HEIGHT-110, 120, 30), "text": "Кавалерия (45g,20w)", "type": UnitType.CAVALRY, "building": BuildingType.STABLE},
        {"rect": pygame.Rect(400, SCREEN_HEIGHT-110, 120, 30), "text": "Лекарь (35g,15w)", "type": UnitType.HEALER, "building": BuildingType.TEMPLE},
        {"rect": pygame.Rect(530, SCREEN_HEIGHT-110, 120, 30), "text": "Осадное (60g,30w,20s)", "type": UnitType.SIEGE, "building": BuildingType.SIEGE_WORKSHOP},
        {"rect": pygame.Rect(660, SCREEN_HEIGHT-110, 120, 30), "text": "Разведчик (20g,5w)", "type": UnitType.SCOUT},
        {"rect": pygame.Rect(790, SCREEN_HEIGHT-110, 120, 30), "text": "Рабочий (20g,10f)", "type": UnitType.WORKER},
        
        {"rect": pygame.Rect(10, SCREEN_HEIGHT-70, 120, 30), "text": "Казармы (100g,50w)", "building_type": BuildingType.BARRACKS},
        {"rect": pygame.Rect(140, SCREEN_HEIGHT-70, 120, 30), "text": "Тир (120g,80w)", "building_type": BuildingType.ARCHERY},
        {"rect": pygame.Rect(270, SCREEN_HEIGHT-70, 120, 30), "text": "Конюшня (150g,100w)", "building_type": BuildingType.STABLE},
        {"rect": pygame.Rect(400, SCREEN_HEIGHT-70, 120, 30), "text": "Храм (130g,60w)", "building_type": BuildingType.TEMPLE},
        {"rect": pygame.Rect(530, SCREEN_HEIGHT-70, 120, 30), "text": "Мастерская (160g,100w,50s)", "building_type": BuildingType.SIEGE_WORKSHOP},
        {"rect": pygame.Rect(660, SCREEN_HEIGHT-70, 120, 30), "text": "Башня (80g,50s)", "building_type": BuildingType.TOWER},
        {"rect": pygame.Rect(790, SCREEN_HEIGHT-70, 120, 30), "text": "Стена (50g,30s)", "building_type": BuildingType.WALL},
        {"rect": pygame.Rect(920, SCREEN_HEIGHT-70, 120, 30), "text": "Ферма (80g,40w)", "building_type": BuildingType.FARM},
        
        {"rect": pygame.Rect(SCREEN_WIDTH-130, SCREEN_HEIGHT-110, 120, 30), "text": "Отменить выбор", "action": "deselect"},
        {"rect": pygame.Rect(SCREEN_WIDTH-130, SCREEN_HEIGHT-70, 120, 30), "text": "Справка (H)", "action": "help"},
        {"rect": pygame.Rect(SCREEN_WIDTH-260, SCREEN_HEIGHT-110, 120, 30), "text": "Туман войны: Вкл", "action": "toggle_fog"},
        {"rect": pygame.Rect(SCREEN_WIDTH-260, SCREEN_HEIGHT-70, 120, 30), "text": "Миникарта: Вкл", "action": "toggle_minimap"}
    ]
    
    help_text = [
        "Управление:",
        "ЛКМ - выделить юнитов/здания, ПКМ - отдать приказ",
        "A - выделить всех юнитов, ESC - выход",
        "R - рестарт после окончания игры",
        "H - показать/скрыть справку",
        "Стрелки - перемещение камеры",
        "",
        "Ресурсы:",
        "- Золото (g) - основная валюта",
        "- Камень (s) - для укреплений",
        "- Дерево (w) - для построек и юнитов",
        "- Еда (f) - для содержания армии",
        "",
        "Юниты:",
        "- Рабочие (W) - собирают все ресурсы",
        "- Шахтеры (M) - специализируются на золоте и камне",
        "- Дровосеки (L) - специализируются на дереве",
        "",
        "Здания:",
        "- Ратуша - производит рабочих, дает доход",
        "- Шахта - производит шахтеров, дает золото и камень",
        "- Лесопилка - производит дровосеков, дает дерево",
        "- Ферма - производит еду"
    ]
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        grid_pos = ((mouse_pos[0] - game.camera_x) // CELL_SIZE, 
                   (mouse_pos[1] - UI_HEIGHT - game.camera_y) // CELL_SIZE if mouse_pos[1] > UI_HEIGHT else (None, None))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    button_clicked = False
                    for button in buttons:
                        if button["rect"].collidepoint(event.pos):
                            button_clicked = True
                            if "type" in button:
                                game.create_unit('player', button["type"])
                                building_mode = None
                            elif "building_type" in button:
                                building_mode = button["building_type"]
                            elif "action" in button:
                                if button["action"] == "deselect":
                                    game.selected_units = []
                                    game.selected_building = None
                                    building_mode = None
                                elif button["action"] == "help":
                                    show_help = not show_help
                                elif button["action"] == "toggle_fog":
                                    game.fog_of_war = not game.fog_of_war
                                    button["text"] = f"Туман войны: {'Выкл' if not game.fog_of_war else 'Вкл'}"
                                elif button["action"] == "toggle_minimap":
                                    game.show_minimap = not game.show_minimap
                                    button["text"] = f"Миникарта: {'Выкл' if not game.show_minimap else 'Вкл'}"
                    
                    if not button_clicked and mouse_pos[1] > UI_HEIGHT:
                        if building_mode is not None:
                            game.build(building_mode, *grid_pos)
                            building_mode = None
                        else:
                            selecting = True
                            # Передаем координаты относительно экрана (без учета камеры)
                            game.selection_start = (mouse_pos[0] // CELL_SIZE, 
                                                (mouse_pos[1] - UI_HEIGHT) // CELL_SIZE)
                            game.selection_end = game.selection_start
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and selecting:
                    selecting = False
                    # Передаем координаты относительно экрана (без учета камеры)
                    game.selection_end = (mouse_pos[0] // CELL_SIZE, 
                                        (mouse_pos[1] - UI_HEIGHT) // CELL_SIZE)
                    if game.selection_start and game.selection_end:
                        game.select_units(game.selection_start, game.selection_end)
                
                elif event.button == 3 and mouse_pos[1] > UI_HEIGHT and building_mode is None:
                    game.command_units(grid_pos)
            
            elif event.type == pygame.MOUSEMOTION and selecting:
                # Обновляем конечную позицию выделения
                game.selection_end = (mouse_pos[0] // CELL_SIZE, 
                                    (mouse_pos[1] - UI_HEIGHT) // CELL_SIZE)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_a:
                    game.selected_units = [u for u in game.player_units if u['build_progress'] >= u['build_time']]
                    game.selected_building = None
                    SELECT_SOUND.play()
                elif event.key == pygame.K_r and game.game_over:
                    game = Game()
                    building_mode = None
                elif event.key == pygame.K_h:
                    show_help = not show_help
                elif event.key == pygame.K_f:
                    game.fog_of_war = not game.fog_of_war
                elif event.key == pygame.K_m:
                    game.show_minimap = not game.show_minimap
                # Управление камерой
                elif event.key == pygame.K_LEFT:
                    game.camera_x = max(0, game.camera_x - CELL_SIZE * 5)
                elif event.key == pygame.K_RIGHT:
                    game.camera_x = min(game.grid_width * CELL_SIZE - SCREEN_WIDTH, game.camera_x + CELL_SIZE * 5)
                elif event.key == pygame.K_UP:
                    game.camera_y = max(0, game.camera_y - CELL_SIZE * 5)
                elif event.key == pygame.K_DOWN:
                    game.camera_y = min(game.grid_height * CELL_SIZE - (SCREEN_HEIGHT - UI_HEIGHT), game.camera_y + CELL_SIZE * 5)
        
        game.update()
        
        screen.fill(BLACK)
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT))
        
        # Отрисовка карты с учетом камеры
        start_x = max(0, int(game.camera_x // CELL_SIZE))
        end_x = min(game.grid_width, start_x + SCREEN_WIDTH // CELL_SIZE + 2)
        start_y = max(0, int(game.camera_y // CELL_SIZE))
        end_y = min(game.grid_height, start_y + (SCREEN_HEIGHT - UI_HEIGHT) // CELL_SIZE + 2)
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                screen_x = x * CELL_SIZE - game.camera_x
                screen_y = y * CELL_SIZE - game.camera_y
                
                if not game.fog_of_war or game.explored[x, y]:
                    terrain = game.terrain[x, y]
                    
                    if terrain < 0.3:
                        color = (50, 50, 150)
                    elif terrain < 0.4:
                        color = (70, 90, 70)
                    elif terrain > 0.8:
                        color = (100, 100, 100)
                    else:
                        color = (30, 80, 30) if (x + y) % 2 == 0 else (40, 90, 40)
                    
                    if game.fog_of_war and not game.vision_map[x, y]:
                        color = tuple(max(0, c - 50) for c in color)
                    
                    pygame.draw.rect(game_surface, color, (screen_x, screen_y, CELL_SIZE, CELL_SIZE))
        
        # Отрисовка сетки
        for x in range(start_x, end_x, 2):
            screen_x = x * CELL_SIZE - game.camera_x
            pygame.draw.line(game_surface, (100, 100, 100, 50), (screen_x, 0), (screen_x, SCREEN_HEIGHT - UI_HEIGHT), 1)
        
        for y in range(start_y, end_y, 2):
            screen_y = y * CELL_SIZE - game.camera_y
            pygame.draw.line(game_surface, (100, 100, 100, 50), (0, screen_y), (SCREEN_WIDTH, screen_y), 1)
        
        # Отрисовка ресурсов
        for resource in game.resources:
            if (start_x <= resource['x'] < end_x and start_y <= resource['y'] < end_y and
                (not game.fog_of_war or game.vision_map[int(resource['x']), int(resource['y'])])):
                screen_x = resource['x'] * CELL_SIZE - game.camera_x
                screen_y = resource['y'] * CELL_SIZE - game.camera_y
                
                # Размер зависит от оставшегося количества
                size = max(3, min(10, int(resource['amount'] / 100)))
                
                if resource['type'] == ResourceType.GOLD:
                    pygame.draw.circle(game_surface, GOLD, (int(screen_x), int(screen_y)), size)
                elif resource['type'] == ResourceType.STONE:
                    pygame.draw.circle(game_surface, STONE, (int(screen_x), int(screen_y)), size)
                elif resource['type'] == ResourceType.WOOD:
                    pygame.draw.rect(game_surface, WOOD, (screen_x-size//2, screen_y-size//2, size, size))
                
                # Отображение количества
                if size > 5:
                    text = small_font.render(str(int(resource['amount'])), True, BLACK)
                    text_rect = text.get_rect(center=(screen_x, screen_y))
                    game_surface.blit(text, text_rect)
        
        # Отрисовка зданий
        for building in game.enemy_buildings + game.player_buildings:
            if (start_x <= building['x'] < end_x and start_y <= building['y'] < end_y and
                (not game.fog_of_war or game.vision_map[int(building['x']), int(building['y'])])):
                size = building['size'] * CELL_SIZE
                screen_x = building['x'] * CELL_SIZE - game.camera_x - size//2
                screen_y = building['y'] * CELL_SIZE - game.camera_y - size//2
                
                if building['side'] == 'player':
                    color = building['color']
                    if building.get('is_base'):
                        color = (0, 200, 200)
                else:
                    color = (200, 100, 100)
                    if building.get('is_base'):
                        color = (200, 0, 0)
                
                alpha = 255 if building['build_progress'] >= building['build_time'] else 128
                
                building_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.rect(building_surface, (*color, alpha), (0, 0, size, size))
                pygame.draw.rect(building_surface, (200, 200, 200, alpha), (0, 0, size, size), 2)
                
                if building['build_progress'] < building['build_time']:
                    progress = building['build_progress'] / building['build_time']
                    pygame.draw.rect(building_surface, (255, 255, 255, alpha), (0, 0, size * progress, 5))
                
                health_ratio = building['health'] / building['max_health']
                health_width = size * health_ratio
                pygame.draw.rect(building_surface, (200, 0, 0, alpha), (0, size-5, size, 5))
                pygame.draw.rect(building_surface, (0, 200, 0, alpha), (0, size-5, health_width, 5))
                
                game_surface.blit(building_surface, (screen_x, screen_y))
                
                if building['build_progress'] >= building['build_time']:
                    type_symbol = ""
                    if building['type'] == BuildingType.BARRACKS: type_symbol = "B"
                    elif building['type'] == BuildingType.ARCHERY: type_symbol = "A"
                    elif building['type'] == BuildingType.STABLE: type_symbol = "S"
                    elif building['type'] == BuildingType.TEMPLE: type_symbol = "H"
                    elif building['type'] == BuildingType.SIEGE_WORKSHOP: type_symbol = "W"
                    elif building['type'] == BuildingType.TOWER: type_symbol = "T"
                    elif building['type'] == BuildingType.WALL: type_symbol = "|"
                    elif building['type'] == BuildingType.TOWN_HALL: type_symbol = "TH"
                    elif building['type'] == BuildingType.MINE: type_symbol = "M"
                    elif building['type'] == BuildingType.LUMBER_MILL: type_symbol = "L"
                    elif building['type'] == BuildingType.FARM: type_symbol = "F"
                    
                    text_color = WHITE if building['side'] == 'player' else BLACK
                    text = small_font.render(type_symbol, True, text_color)
                    text_rect = text.get_rect(center=(building['x']*CELL_SIZE - game.camera_x, 
                                                     building['y']*CELL_SIZE - game.camera_y))
                    game_surface.blit(text, text_rect)
        
        # Отрисовка юнитов
        for unit in game.enemy_units + game.player_units:
            if (unit['build_progress'] >= unit['build_time'] and
                start_x <= unit['x'] < end_x and start_y <= unit['y'] < end_y):
                
                visible = False
                if not game.fog_of_war:
                    visible = True
                elif game.vision_map[int(unit['x']), int(unit['y'])]:
                    visible = True
                elif unit['side'] == 'enemy' and game.explored[int(unit['x']), int(unit['y'])]:
                    visible = True
                    
                if visible:
                    size = CELL_SIZE - 2
                    screen_x = unit['x'] * CELL_SIZE - game.camera_x - size//2
                    screen_y = unit['y'] * CELL_SIZE - game.camera_y - size//2
                    
                    color = unit['color'] if unit['side'] == 'player' else YELLOW
                    
                    pygame.draw.rect(game_surface, color, (screen_x, screen_y, size, size))
                    pygame.draw.rect(game_surface, WHITE if unit['side'] == 'player' else BLACK, 
                                   (screen_x, screen_y, size, size), 1)
                    
                    health_ratio = unit['health'] / unit['max_health']
                    health_width = size * health_ratio
                    pygame.draw.rect(game_surface, RED, (screen_x, screen_y-5, size, 3))
                    pygame.draw.rect(game_surface, GREEN, (screen_x, screen_y-5, health_width, 3))
                    
                    type_symbol = ""
                    if unit['type'] == UnitType.WARRIOR: type_symbol = "W"
                    elif unit['type'] == UnitType.ARCHER: type_symbol = "A"
                    elif unit['type'] == UnitType.CAVALRY: type_symbol = "C"
                    elif unit['type'] == UnitType.HEALER: type_symbol = "H"
                    elif unit['type'] == UnitType.SIEGE: type_symbol = "S"
                    elif unit['type'] == UnitType.SCOUT: type_symbol = "R"
                    elif unit['type'] == UnitType.WORKER: type_symbol = "Wk"
                    elif unit['type'] == UnitType.MINER: type_symbol = "M"
                    elif unit['type'] == UnitType.LUMBERJACK: type_symbol = "L"
                    
                    text_color = WHITE if unit['side'] == 'player' else BLACK
                    text = small_font.render(type_symbol, True, text_color)
                    text_rect = text.get_rect(center=(unit['x']*CELL_SIZE - game.camera_x, 
                                                    unit['y']*CELL_SIZE - game.camera_y))
                    game_surface.blit(text, text_rect)
                    
                    # Отображение переносимых ресурсов
                    if any(unit['carrying'].values()):
                        res_text = ""
                        for res, amount in unit['carrying'].items():
                            if amount > 0:
                                res_text += f"{res[0]}:{amount} "
                        
                        if res_text:
                            res_surface = small_font.render(res_text, True, WHITE)
                            game_surface.blit(res_surface, (screen_x, screen_y - 15))
        
        # Отрисовка частиц
        for particle in game.particles:
            if (start_x <= particle['x'] < end_x and start_y <= particle['y'] < end_y and
                (not game.fog_of_war or game.vision_map[
                    int(max(0, min(game.grid_width-1, particle['x']))), 
                    int(max(0, min(game.grid_height-1, particle['y'])))
                ])):
                screen_x = particle['x'] * CELL_SIZE - game.camera_x
                screen_y = particle['y'] * CELL_SIZE - game.camera_y
                pygame.draw.circle(game_surface, particle['color'], (int(screen_x), int(screen_y)), particle['size'])
        
        # Отрисовка выделения
        if selecting and game.selection_start and game.selection_end:
            x1, y1 = game.selection_start
            x2, y2 = game.selection_end
            left = min(x1, x2) * CELL_SIZE
            right = max(x1, x2) * CELL_SIZE + CELL_SIZE
            top = min(y1, y2) * CELL_SIZE
            bottom = max(y1, y2) * CELL_SIZE + CELL_SIZE
            
            selection_surface = pygame.Surface((right - left, bottom - top), pygame.SRCALPHA)
            selection_surface.fill(LIGHT_BLUE)
            game_surface.blit(selection_surface, (left, top))
            pygame.draw.rect(game_surface, BLUE, (left, top, right - left, bottom - top), 2)
        
        # Отрисовка выделенных юнитов
        for unit in game.selected_units:
            if unit['build_progress'] >= unit['build_time']:
                size = CELL_SIZE
                screen_x = unit['x'] * CELL_SIZE - game.camera_x - size//2
                screen_y = unit['y'] * CELL_SIZE - game.camera_y - size//2
                pygame.draw.rect(game_surface, BLUE, 
                               (screen_x, screen_y, size, size), 2)
        
        # Отрисовка выделенного здания
        if game.selected_building:
            size = game.selected_building['size'] * CELL_SIZE
            screen_x = game.selected_building['x'] * CELL_SIZE - game.camera_x - size//2
            screen_y = game.selected_building['y'] * CELL_SIZE - game.camera_y - size//2
            pygame.draw.rect(game_surface, BLUE, (screen_x, screen_y, size, size), 3)
        
        # Отрисовка режима строительства
        if building_mode is not None and mouse_pos[1] > UI_HEIGHT:
            stats = game.get_building_stats(building_mode)
            if stats:
                size = stats['size'] * CELL_SIZE
                screen_x = grid_pos[0] * CELL_SIZE - game.camera_x - size//2
                screen_y = grid_pos[1] * CELL_SIZE - game.camera_y - size//2
                
                can_build = True
                for building in game.player_buildings + game.enemy_buildings:
                    if game.get_distance(grid_pos[0], grid_pos[1], building['x'], building['y']) < max(stats['size'], building['size']) + 2:
                        can_build = False
                        break
                
                if (grid_pos[0] - stats['size']/2 < 0 or grid_pos[0] + stats['size']/2 >= game.grid_width or
                    grid_pos[1] - stats['size']/2 < 0 or grid_pos[1] + stats['size']/2 >= game.grid_height):
                    can_build = False
                
                color = GREEN if can_build else RED
                alpha = 100 if can_build else 70
                
                building_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.rect(building_surface, (*color, alpha), (0, 0, size, size))
                pygame.draw.rect(building_surface, (*WHITE, alpha), (0, 0, size, size), 2)
                game_surface.blit(building_surface, (screen_x, screen_y))
        
        screen.blit(game_surface, (0, UI_HEIGHT))
        
        # Отрисовка интерфейса
        pygame.draw.rect(screen, DARK_GREEN, (0, 0, SCREEN_WIDTH, UI_HEIGHT))
        
        stats = [
            f"Ход: {game.turn}",
            f"Игрок: {len(game.player_units)} юнитов | Ресурсы: G:{int(game.player_resources['gold'])}, S:{int(game.player_resources['stone'])}, W:{int(game.player_resources['wood'])}, F:{int(game.player_resources['food'])}",
            f"База: {int(game.player_base['health'])}/{game.player_base['max_health']} HP",
            f"Враг: {len(game.enemy_units)} юнитов | Ресурсы: G:{int(game.enemy_resources['gold'])}, S:{int(game.enemy_resources['stone'])}, W:{int(game.enemy_resources['wood'])}, F:{int(game.enemy_resources['food'])}",
            f"База врага: {int(game.enemy_base['health'])}/{game.enemy_base['max_health']} HP",
            f"Выделено: {len(game.selected_units)} юнитов" + (f" | Здание: {game.selected_building['type'].name if game.selected_building else ''}" if game.selected_building else "")
        ]
        
        for i, text in enumerate(stats):
            text_surface = font.render(text, True, WHITE)
            screen.blit(text_surface, (10, 10 + i*20))
        
        # Отрисовка кнопок
        for button in buttons:
            if button.get("building_type") == building_mode:
                color = (0, 150, 0)
            elif button.get("type") and not game.can_afford('player', game.get_unit_stats(button["type"])["cost"]):
                color = (100, 100, 100)
            elif button.get("building_type") and not game.can_afford('player', game.get_building_stats(button["building_type"])["cost"]):
                color = (100, 100, 100)
            elif button["rect"].collidepoint(mouse_pos):
                color = (0, 0, 150)
            else:
                color = (0, 0, 100)
            
            draw_rounded_rect(screen, color, button["rect"], 5)
            
            text_surface = small_font.render(button["text"], True, WHITE)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            screen.blit(text_surface, text_rect)
        
        # Отрисовка миникарты
        if game.show_minimap:
            minimap_rect = pygame.Rect(SCREEN_WIDTH - MINIMAP_SIZE - 10, UI_HEIGHT + 10, MINIMAP_SIZE, MINIMAP_SIZE)
            pygame.draw.rect(screen, BLACK, minimap_rect)
            pygame.draw.rect(screen, WHITE, minimap_rect, 2)
            
            scale_x = MINIMAP_SIZE / game.grid_width
            scale_y = MINIMAP_SIZE / game.grid_height
            
            for x in range(game.grid_width):
                for y in range(game.grid_height):
                    if game.explored[x, y]:
                        color = (0, 80, 0) if game.terrain[x, y] > 0.4 else (0, 0, 80)
                        if game.vision_map[x, y]:
                            color = (0, 150, 0) if game.terrain[x, y] > 0.4 else (0, 0, 150)
                        
                        pygame.draw.rect(screen, color, 
                                       (SCREEN_WIDTH - MINIMAP_SIZE - 10 + x * scale_x,
                                        UI_HEIGHT + 10 + y * scale_y,
                                        max(1, scale_x), max(1, scale_y)))
            
            for unit in game.player_units + game.enemy_units:
                if unit['build_progress'] >= unit['build_time'] and game.explored[int(unit['x']), int(unit['y'])]:
                    color = BLUE if unit['side'] == 'player' else YELLOW
                    pygame.draw.circle(screen, color,
                                      (int(SCREEN_WIDTH - MINIMAP_SIZE - 10 + unit['x'] * scale_x),
                                      int(UI_HEIGHT + 10 + unit['y'] * scale_y)),
                                      max(1, int(scale_x * 1.5)))
            
            for building in game.player_buildings + game.enemy_buildings:
                if building['build_progress'] >= building['build_time'] and game.explored[int(building['x']), int(building['y'])]:
                    color = GREEN if building['side'] == 'player' else RED
                    if building.get('is_base'):
                        color = CYAN if building['side'] == 'player' else (200, 0, 0)
                    
                    size = max(2, int(building['size'] * scale_x))
                    pygame.draw.rect(screen, color,
                                    (SCREEN_WIDTH - MINIMAP_SIZE - 10 + building['x'] * scale_x - size//2,
                                     UI_HEIGHT + 10 + building['y'] * scale_y - size//2,
                                     size, size))
            
            for resource in game.resources:
                if game.explored[int(resource['x']), int(resource['y'])]:
                    color = resource['color']
                    pygame.draw.circle(screen, color,
                                     (int(SCREEN_WIDTH - MINIMAP_SIZE - 10 + resource['x'] * scale_x),
                                     int(UI_HEIGHT + 10 + resource['y'] * scale_y)),
                                     max(1, int(scale_x)))
            
            # Прямоугольник видимой области на миникарте
            view_rect = pygame.Rect(
                SCREEN_WIDTH - MINIMAP_SIZE - 10 + (game.camera_x / game.grid_width) * MINIMAP_SIZE,
                UI_HEIGHT + 10 + (game.camera_y / game.grid_height) * MINIMAP_SIZE,
                (SCREEN_WIDTH / game.grid_width) * scale_x,
                ((SCREEN_HEIGHT - UI_HEIGHT) / game.grid_height) * scale_y
            )
            pygame.draw.rect(screen, WHITE, view_rect, 1)
        
        # Отрисовка справки
        if show_help:
            help_surface = pygame.Surface((600, 500), pygame.SRCALPHA)
            help_surface.fill((0, 0, 0, 200))
            pygame.draw.rect(help_surface, (0, 0, 100, 200), (0, 0, 600, 500), 2)
            
            title = big_font.render("Справка", True, WHITE)
            help_surface.blit(title, (300 - title.get_width()//2, 20))
            
            for i, line in enumerate(help_text):
                text = font.render(line, True, WHITE)
                help_surface.blit(text, (20, 80 + i*25))
            
            screen.blit(help_surface, (SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT//2 - 250))
        
        # Отрисовка окончания игры
        if game.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            text = big_font.render(game.game_over, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(text, text_rect)
            
            restart_text = font.render("Нажмите R для рестарта", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
