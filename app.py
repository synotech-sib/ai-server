import random

class Creature:
    def __init__(self, x, y, is_altruist=False):
        self.x = x
        self.y = y
        self.energy = 50  # 초기 에너지
        self.is_altruist = is_altruist
        self.is_alive = True

    def move(self, grid_size):
        # 이동 시 에너지 소모 (Step 11의 핵심: 에너지 효율)
        move_cost = 2
        if self.energy >= move_cost:
            self.energy -= move_cost
            self.x = (self.x + random.randint(-1, 1)) % grid_size
            self.y = (self.y + random.randint(-1, 1)) % grid_size
        else:
            self.is_alive = False

    def eat(self, food_grid):
        if food_grid[self.x][self.y] > 0:
            self.energy += 30
            food_grid[self.x][self.y] -= 1
            return True
        return False

    def share_energy(self, neighbors):
        # 알트리스 로직: 주변에 에너지가 낮은 개체가 있다면 나눠줌
        if self.is_altruist and self.energy > 40:
            for neighbor in neighbors:
                if neighbor.energy < 20:
                    transfer = 10
                    self.energy -= transfer
                    neighbor.energy += transfer
                    break

class Simulation:
    def __init__(self, grid_size=20, num_creatures=10, altruist_ratio=0.3):
        self.grid_size = grid_size
        self.food_grid = [[1 for _ in range(grid_size)] for _ in range(grid_size)]
        self.creatures = []
        
        for _ in range(num_creatures):
            is_alt = random.random() < altruist_ratio
            self.creatures.append(Creature(random.randint(0, grid_size-1), 
                                           random.randint(0, grid_size-1), is_alt))

    def run_step(self):
        # 1. 이동 및 식사
        for c in self.creatures:
            if c.is_alive:
                c.move(self.grid_size)
                c.eat(self.food_grid)

        # 2. 알트리스 상호작용
        for c in self.creatures:
            if c.is_alive and c.is_altruist:
                neighbors = [other for other in self.creatures if other != c and other.is_alive 
                             and abs(other.x - c.x) <= 1 and abs(other.y - c.y) <= 1]
                c.share_energy(neighbors)

        # 3. 생존 확인 및 자원 재생성
        self.creatures = [c for c in self.creatures if c.energy > 0]
        if random.random() < 0.2: # 20% 확률로 무작위 위치에 음식 생성
            self.food_grid[random.randint(0, 19)][random.randint(0, 19)] += 1

    def report(self):
        alt_count = sum(1 for c in self.creatures if c.is_altruist)
        ego_count = len(self.creatures) - alt_count
        print(f"현재 생존자: {len(self.creatures)} (알트리스: {alt_count}, 이기주의자: {ego_count})")

# 실행부
sim = Simulation(num_creatures=20, altruist_ratio=0.4)
for day in range(1, 11):
    print(f"--- Day {day} ---")
    sim.run_step()
    sim.report()