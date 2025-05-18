from ursina import *
from ursina.prefabs.first_person_controller import  FirstPersonController
from noise import pnoise2
import random
from math import inf

app = Ursina()
Sky(texture='sky_default')
AmbientLight()
# Constants
CHUNK_SIZE = 8
RENDER_DISTANCE = 1
PLAYER_HEIGHT = 2
GRAVITY = 0.3
MIN_HEIGHT = 0
MAX_BLOCK_REACH = 5
SPAWN_HEIGHT = 1
UPDATE_INTERVAL = 0.1

# Initialize random seed
seed = 5000
print(f"Seed: {seed}")

# Terrain types with their parameters
TERRAIN_TYPES = {
    '1': {
        'name': 'Plains',
        'scale': 15.0,
        'octaves': 3,
        'height_scale': 4,
        'persistence': 0.5,
        'base_height': 2,
        'lacunarity': 2.0,
        'generator': lambda x, z, seed: (
                pnoise2(x/25.0, z/25.0, octaves=1, persistence=0.5, base=seed) * 4
        )
    },
    '2': {
        'name': 'Mountains',
        'scale': 8.0,
        'octaves': 4,
        'height_scale': 15,
        'persistence': 0.5,
        'base_height': 5,
        'lacunarity': 2.5,
        'generator': lambda x, z, seed: (
                pnoise2(x/8.0, z/8.0, octaves=4, persistence=0.5, base=seed) * 15 + 5
        )
    },
    '3': {
        'name': 'Hills',
        'scale': 12.0,
        'octaves': 2,
        'height_scale': 8,
        'persistence': 0.6,
        'base_height': 2,
        'lacunarity': 1.8,
        'generator': lambda x, z, seed: (
                pnoise2(x/12.0, z/12.0, octaves=2, persistence=0.6, base=seed) * 8 + 2
        )
    },
    '4': {
        'name': 'Desert',
        'scale': 15.0,
        'octaves': 1,
        'height_scale': 6,
        'persistence': 0.3,
        'base_height': 1,
        'lacunarity': 1.5,
        'generator': lambda x, z, seed: (
                pnoise2(x/15.0, z/15.0, octaves=3, persistence=0.3, base=seed) * 6 + 1
        )
    },
    '5': {
        'name': 'Jagged Mountains',
        'scale': 6.0,
        'octaves': 6,
        'height_scale': 20,
        'persistence': 0.7,
        'base_height': 8,
        'lacunarity': 3.0,
        'generator': lambda x, z, seed: (
                pnoise2(x/6.0, z/6.0, octaves=6, persistence=0.7, base=seed) * 20 + 8 +
                abs(pnoise2(x/3.0, z/3.0, octaves=2, base=seed+1)) * 8
        )
    },
    '6': {
        'name': 'Archipelago',
        'scale': 20.0,
        'octaves': 3,
        'height_scale': 12,
        'persistence': 0.5,
        'base_height': 3,
        'lacunarity': 2.2,
        'generator': lambda x, z, seed: (
            max(0, pnoise2(x/20.0, z/20.0, octaves=3, persistence=0.5, base=seed) * 12 - 3)
        )
    },
    '7': {
        'name': 'Canyon Lands',
        'scale': 12.0,
        'octaves': 2,
        'height_scale': 15,
        'persistence': 0.6,
        'base_height': 5,
        'lacunarity': 2.8,
        'generator': lambda x, z, seed: (
                abs(pnoise2(x/12.0, z/12.0, octaves=2, persistence=0.6, base=seed)) * 15 +
                pnoise2(x/6.0, z/6.0, octaves=1, base=seed+1) * 4 + 5
        )
    },
    '8': {
        'name': 'Volcanic',
        'scale': 15.0,
        'octaves': 4,
        'height_scale': 25,
        'persistence': 0.5,
        'base_height': 3,
        'lacunarity': 2.4,
        'generator': lambda x, z, seed: (
            max(0, pnoise2(x/15.0, z/15.0, octaves=4, persistence=0.5, base=seed) * 25 +
                (15 - ((x*x + z*z) ** 0.5) / 4) +
                pnoise2(x/8.0, z/8.0, octaves=2, base=seed+1) * 3)
        )
    }
}

# Load textures
textures = {
    'mountain': load_texture('mountain_block.png'),
    'wood': load_texture('wood.jpeg'),
    'snow': load_texture('snow.png'),
#   ------ You can add these later!! -----
    'grass': load_texture('grass.png'),
    'dirt': load_texture('dirt_block.png'),
    # 'stone': load_texture('stone.png'),
    # 'sand': load_texture('sand.png'),
    # 'water': load_texture('water.png'),
    # 'lava': load_texture('lava.png'),
}

# Global variables
active_chunks = {}
terrain_blocks = {}
current_terrain = '1'
selected_block_type = 'mountain'
selected_slot = 0
chunk_parent = Entity()
# add cube children to chunk_parent
chunk_parent.combine()
# Inventory setup
inventory_items = ['mountain', 'wood', 'snow', 'dirt', 'grass']
inventory_slots = []

# Block selector entity
block_selector = Entity(model='cube', color=color.rgba(1, 1, 1, 0.2), scale=1.01)
def get_biome_noise(x, z):
    return pnoise2(
        x / 100.0,
        z / 100.0,
        octaves=2,
        persistence=0.5,
        lacunarity=2.0,
        repeatx=99999,
        repeaty=99999,
        base=42
    )

def get_temperature(x, z):
    return pnoise2(
        x / 150.0,
        z / 150.0,
        octaves=1,
        persistence=0.5,
        lacunarity=2.0,
        repeatx=inf,
        repeaty=inf,
        base=123
    )

def get_moisture(x, z):
    return pnoise2(
        x / 150.0,
        z / 150.0,
        octaves=1,
        persistence=0.5,
        lacunarity=2.0,
        repeatx=inf,
        repeaty=inf,
        base=321
    )

def get_biome(x, z):
    temperature = get_temperature(x, z)
    moisture = get_moisture(x, z)

    # Scale values to 0-1 range if they aren't already
    temperature = (temperature + 1) / 2
    moisture = (moisture + 1) / 2

    # More granular biome selection
    if temperature < 0.2:
        if moisture < 0.3:
            return '1'  # Plains
        else:
            return '3'  # Hills
    elif temperature < 0.4:
        if moisture < 0.4:
            return '4'  # Desert
        else:
            return '2'  # Mountains
    elif temperature < 0.6:
        if moisture < 0.5:
            return '7'  # Canyon Lands
        else:
            return '5'  # Jagged Mountains
    elif temperature < 0.8:
        return '8'  # Volcanic
    else:
        return '6'  # Archipelago
def get_height(x, z):
    biome = get_biome(x, z)
    biome_data = TERRAIN_TYPES[biome]

    nearby_biomes = []
    for dx in [-1, 0, 1]:
        for dz in [-1, 0, 1]:
            nearby_biomes.append(get_biome(x + dx * 10, z + dz * 10))

    # Use the generator function from the biome data
    height = biome_data['generator'](x, z, seed)

    # Blend with nearby biomes
    blend_factor = 0.5 + get_biome_noise(x, z) * 0.5

    for nearby_biome in nearby_biomes:
        if nearby_biome != biome:
            nearby_data = TERRAIN_TYPES[nearby_biome]
            nearby_height = nearby_data['generator'](x, z, seed)
            height = height * blend_factor + nearby_height * (1 - blend_factor)

    return int(height)


def create_block(position, block_type='grass'):
    x, y, z = position
    if y >= 9:
        block_type = 'snow'
    if 0 < y < 9:
        block_type = 'grass'
    if y == 0:
        block_type = 'dirt'
    return Entity(
        model='cube',
        texture=textures[block_type],
        position=(round(x), round(y), round(z)),
        scale=Vec3(1, 1, 1),
        collider='box',
        static=True,
        collision=True,
        highlight_color=color.rgba(1, 1, 1, 0.2)
    )

def generate_chunk(chunk_x, chunk_z):
    if (chunk_x, chunk_z) in active_chunks:
        return

    blocks = []

    for x in range(CHUNK_SIZE):
        for z in range(CHUNK_SIZE):
            world_x = chunk_x * CHUNK_SIZE + x
            world_z = chunk_z * CHUNK_SIZE + z
            height = max(0, get_height(world_x, world_z))

            for y in range(height + 1):
                block_pos = (world_x, y, world_z)
                block = create_block(block_pos, 'mountain')
                blocks.append(block)
                terrain_blocks[block_pos] = block

    active_chunks[(chunk_x, chunk_z)] = blocks

def remove_distant_chunks():
    player_chunk_x = int(player.x // CHUNK_SIZE)
    player_chunk_z = int(player.z // CHUNK_SIZE)

    chunks_to_remove = []
    for chunk_pos in active_chunks:
        chunk_x, chunk_z = chunk_pos
        distance = max(abs(chunk_x - player_chunk_x), abs(chunk_z - player_chunk_z))
        if distance > RENDER_DISTANCE:
            chunks_to_remove.append(chunk_pos)

    for chunk_pos in chunks_to_remove:
        for block in active_chunks[chunk_pos]:
            if block.position in terrain_blocks:
                del terrain_blocks[block.position]
            destroy(block)
        del active_chunks[chunk_pos]

def update_chunks():
    player_chunk_x = int(player.x // CHUNK_SIZE)
    player_chunk_z = int(player.z // CHUNK_SIZE)

    for chunk_x in range(player_chunk_x - RENDER_DISTANCE, player_chunk_x + RENDER_DISTANCE + 1):
        for chunk_z in range(player_chunk_z - RENDER_DISTANCE, player_chunk_z + RENDER_DISTANCE + 1):
            generate_chunk(chunk_x, chunk_z)

    remove_distant_chunks()

def regenerate_terrain():
    # Clear existing terrain
    for chunk_blocks in active_chunks.values():
        for block in chunk_blocks:
            destroy(block)
    active_chunks.clear()
    terrain_blocks.clear()

    # Generate new terrain around player
    update_chunks()

def add_block(position):
    if position in terrain_blocks:
        return

    block = create_block(position, selected_block_type)
    terrain_blocks[position] = block
    chunk_x = int(position[0] // CHUNK_SIZE)
    chunk_z = int(position[2] // CHUNK_SIZE)

    if (chunk_x, chunk_z) in active_chunks:
        active_chunks[(chunk_x, chunk_z)].append(block)

def remove_block(position):
    if position in terrain_blocks:
        block = terrain_blocks[position]
        chunk_x = int(position[0] // CHUNK_SIZE)
        chunk_z = int(position[2] // CHUNK_SIZE)

        if (chunk_x, chunk_z) in active_chunks:
            active_chunks[(chunk_x, chunk_z)].remove(block)

        destroy(block)
        del terrain_blocks[position]

def round_position(pos):
    return Vec3(round(pos.x), round(pos.y), round(pos.z))

def input(key):
    global current_terrain, selected_block_type, selected_slot

    # Terrain type selection
    if held_keys['shift']:
        for i in range(1, 9):
            if key == str(i):
                current_terrain = str(i)
                print(f"Switched to {TERRAIN_TYPES[current_terrain]['name']} terrain")
                regenerate_terrain()
                return

    # Block type selection
    elif key.isdigit() and int(key) <= len(inventory_items):
        selected_slot = int(key) - 1
        selected_block_type = inventory_items[selected_slot]
        print(f"Selected block: {selected_block_type}")

# Initialize sky

# Initialize spawn position
spawn_x = 0
spawn_z = 0
terrain_height = get_height(spawn_x, spawn_z)
spawn_y = terrain_height + SPAWN_HEIGHT


# Create player
player = FirstPersonController(
    position=(spawn_x, SPAWN_HEIGHT, spawn_z),
    gravity=GRAVITY,
    jump_height=1.5,
    jump_duration=0.35,
    walking_speed=8,
    model='cube',
    collider='box',
    visible=False,
    running_speed=12,
    mouse_sensitivity=Vec2(50, 50),
    grounded=False,
    collisions=True,
    height=1.8
)

# Initialize chunk update delay
chunk_update_delay = 0

def update():
    global chunk_update_delay   
    # Ray casting for block selection
    ray = raycast(
        player.position + Vec3(0, 2, 0),
        player.forward,
        distance=MAX_BLOCK_REACH,
        ignore=[player]
    )

    if ray.hit:
        hit_pos = ray.world_point
        hit_normal = ray.world_normal
        block_pos = Vec3(round(ray.entity.x), round(ray.entity.y), round(ray.entity.z))
        place_pos = Vec3(
            round(hit_pos.x + hit_normal.x),
            round(hit_pos.y + hit_normal.y),
            round(hit_pos.z + hit_normal.z)
        )

        block_selector.visible = True
        block_selector.position = block_pos

        if held_keys['left mouse']:
            remove_block(tuple(block_pos))
        if held_keys['right mouse']:
            add_block(tuple(place_pos))
    else:
        block_selector.visible = False

    # Update chunks
    chunk_update_delay += time.dt
    if chunk_update_delay >= UPDATE_INTERVAL:
        update_chunks()
        chunk_update_delay = 0

    # Get current terrain height at player position
    x, z = int(player.x), int(player.z)
    current_terrain_height = get_height(x, z)

    # Flying controls
    if held_keys['shift'] and not any(held_keys[str(i)] for i in range(1, 9)):
        player.y += 5 * time.dt
        player.gravity = 0
    elif held_keys['control']:
        player.y -= 5 * time.dt
        player.gravity = 0
    else:
        player.gravity = GRAVITY

        # Improved ground check
        if player.y < current_terrain_height + MIN_HEIGHT:
            player.y = current_terrain_height + MIN_HEIGHT
            player.grounded = True
        else:
            player.grounded = False

    # Reset position if fallen through terrain or below world
    if player.y < current_terrain_height or player.y < 0:
        new_spawn_height = get_height(spawn_x, spawn_z) + SPAWN_HEIGHT
        player.position = (spawn_x, new_spawn_height, spawn_z)
        player.grounded = False

# Create simple UI text for current terrain type
terrain_text = Text(
    text=f"Current Terrain: {TERRAIN_TYPES[current_terrain]['name']}",
    position=(-0.85, 0.45),
    scale=1.5
)

def update_terrain_text():
    terrain_text.text = f"Current Terrain: {TERRAIN_TYPES[current_terrain]['name']}"

# Instructions text
instructions = Text(
    text="WASD to move\nSpace to jump\nShift + 1-8 to change terrain\nLeft click to break\nRight click to place\nShift to fly up\nControl to fly down",
    position=(-0.85, 0.35),
    scale=1
)

# Generate initial terrain
update_chunks()

# Run the application
app.run()
