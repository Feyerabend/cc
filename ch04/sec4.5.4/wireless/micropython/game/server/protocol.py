"""
Shared protocol for Dogfight multiplayer game
Used by both server and clients

Improved with better validation and error handling
"""

import struct

# Packet type constants
PKT_CLIENT_INPUT = 0x01
PKT_FULL_STATE = 0x02
PKT_DELTA_STATE = 0x03
PKT_PING = 0x04
PKT_PONG = 0x05
PKT_CLIENT_CONNECT = 0x06
PKT_CLIENT_ACK = 0x07

# Game constants
GAME_WIDTH = 100
GAME_HEIGHT = 80

# Direction constants
DIR_N, DIR_NE, DIR_E, DIR_SE = 0, 1, 2, 3
DIR_S, DIR_SW, DIR_W, DIR_NW = 4, 5, 6, 7

DIR_DX = [0, 1, 1, 1, 0, -1, -1, -1]
DIR_DY = [-1, -1, 0, 1, 1, 1, 0, -1]

class ClientInputPacket:
    """Client -> Server: Button states"""
    FORMAT = "!BBBBBBxx"
    SIZE = struct.calcsize(FORMAT)
    
    @staticmethod
    def pack(player_id, btn_a, btn_b, btn_x, btn_y):
        return struct.pack(
            ClientInputPacket.FORMAT,
            PKT_CLIENT_INPUT,
            player_id,
            1 if btn_a else 0,
            1 if btn_b else 0,
            1 if btn_x else 0,
            1 if btn_y else 0
        )
    
    @staticmethod
    def unpack(data):
        if len(data) < ClientInputPacket.SIZE:
            raise ValueError("Packet too short")
        
        pkt_type, player_id, btn_a, btn_b, btn_x, btn_y = struct.unpack(
            ClientInputPacket.FORMAT, data[:ClientInputPacket.SIZE]
        )
        return {
            'player_id': player_id,
            'btn_a': bool(btn_a),
            'btn_b': bool(btn_b),
            'btn_x': bool(btn_x),
            'btn_y': bool(btn_y)
        }

class ConnectPacket:
    """Connection handshake"""
    FORMAT = "!BB6x"
    SIZE = struct.calcsize(FORMAT)
    
    @staticmethod
    def pack_request():
        return struct.pack(ConnectPacket.FORMAT, PKT_CLIENT_CONNECT, 0)
    
    @staticmethod
    def pack_ack(player_id):
        if player_id not in [1, 2]:
            raise ValueError(f"Invalid player_id: {player_id}")
        return struct.pack(ConnectPacket.FORMAT, PKT_CLIENT_ACK, player_id)
    
    @staticmethod
    def unpack(data):
        if len(data) < ConnectPacket.SIZE:
            raise ValueError("Packet too short")
        
        pkt_type, player_id = struct.unpack(
            ConnectPacket.FORMAT, data[:ConnectPacket.SIZE]
        )
        return {'type': pkt_type, 'player_id': player_id}

class FullStatePacket:
    """Server -> Client: Complete game state"""
    HEADER_FORMAT = "!BHBBBB"
    PLAYER_FORMAT = "BBB"
    SHOT_FORMAT = "BBBBB"
    
    @staticmethod
    def pack(seq, p1_state, p2_state, p1_shots, p2_shots, game_over=False, winner=0):
        data = struct.pack(
            FullStatePacket.HEADER_FORMAT,
            PKT_FULL_STATE,
            seq,
            1 if p1_state['alive'] else 0,
            1 if p2_state['alive'] else 0,
            1 if game_over else 0,
            winner
        )
        
        data += struct.pack(
            FullStatePacket.PLAYER_FORMAT,
            p1_state['x'],
            p1_state['y'],
            p1_state['dir']
        )
        
        data += struct.pack(
            FullStatePacket.PLAYER_FORMAT,
            p2_state['x'],
            p2_state['y'],
            p2_state['dir']
        )
        
        data += struct.pack("BB", len(p1_shots), len(p2_shots))
        
        for shot in p1_shots:
            data += struct.pack(
                FullStatePacket.SHOT_FORMAT,
                shot['x'], shot['y'], shot['dir'], shot['range'], 1
            )
        
        for shot in p2_shots:
            data += struct.pack(
                FullStatePacket.SHOT_FORMAT,
                shot['x'], shot['y'], shot['dir'], shot['range'], 2
            )
        
        return data
    
    @staticmethod
    def unpack(data):
        try:
            offset = 0
            header_size = struct.calcsize(FullStatePacket.HEADER_FORMAT)
            
            if len(data) < header_size:
                raise ValueError("Packet too short for header")
            
            pkt_type, seq, p1_alive, p2_alive, game_over, winner = struct.unpack(
                FullStatePacket.HEADER_FORMAT,
                data[offset:offset+header_size]
            )
            offset += header_size
            
            player_size = struct.calcsize(FullStatePacket.PLAYER_FORMAT)
            
            if len(data) < offset + 2 * player_size:
                raise ValueError("Packet too short for player data")
            
            p1_x, p1_y, p1_dir = struct.unpack(
                FullStatePacket.PLAYER_FORMAT,
                data[offset:offset+player_size]
            )
            offset += player_size
            
            p2_x, p2_y, p2_dir = struct.unpack(
                FullStatePacket.PLAYER_FORMAT,
                data[offset:offset+player_size]
            )
            offset += player_size
            
            if len(data) < offset + 2:
                raise ValueError("Packet too short for shot counts")
            
            p1_shot_count, p2_shot_count = struct.unpack("BB", data[offset:offset+2])
            offset += 2
            
            shots = []
            shot_size = struct.calcsize(FullStatePacket.SHOT_FORMAT)
            total_shots = p1_shot_count + p2_shot_count
            
            if len(data) < offset + total_shots * shot_size:
                raise ValueError("Packet too short for shots")
            
            for _ in range(total_shots):
                x, y, dir, range, owner = struct.unpack(
                    FullStatePacket.SHOT_FORMAT,
                    data[offset:offset+shot_size]
                )
                shots.append({
                    'x': x, 'y': y, 'dir': dir, 
                    'range': range, 'owner': owner
                })
                offset += shot_size
            
            return {
                'seq': seq,
                'p1': {'x': p1_x, 'y': p1_y, 'dir': p1_dir, 'alive': bool(p1_alive)},
                'p2': {'x': p2_x, 'y': p2_y, 'dir': p2_dir, 'alive': bool(p2_alive)},
                'shots': shots,
                'game_over': bool(game_over),
                'winner': winner
            }
        except Exception as e:
            print(f"Error unpacking full state: {e}")
            return None

class DeltaStatePacket:
    """Server -> Client: Incremental updates"""
    HEADER_FORMAT = "!BHB"
    POSITION_FORMAT = "BBB"
    SHOT_ADD_FORMAT = "BBBBB"
    SHOT_REMOVE_FORMAT = "BB"
    
    FLAG_P1_POS = 0x01
    FLAG_P2_POS = 0x02
    FLAG_P1_DIR = 0x04
    FLAG_P2_DIR = 0x08
    FLAG_GAME_OVER = 0x10
    
    @staticmethod
    def pack(seq, p1_pos=None, p2_pos=None, shots_added=None, shots_removed=None, game_over=False, winner=0):
        flags = 0
        if p1_pos: flags |= DeltaStatePacket.FLAG_P1_POS
        if p2_pos: flags |= DeltaStatePacket.FLAG_P2_POS
        if p1_pos and 'dir' in p1_pos: flags |= DeltaStatePacket.FLAG_P1_DIR
        if p2_pos and 'dir' in p2_pos: flags |= DeltaStatePacket.FLAG_P2_DIR
        if game_over: flags |= DeltaStatePacket.FLAG_GAME_OVER
        
        data = struct.pack(DeltaStatePacket.HEADER_FORMAT, PKT_DELTA_STATE, seq, flags)
        
        if p1_pos:
            data += struct.pack("BB", p1_pos['x'], p1_pos['y'])
            if 'dir' in p1_pos:
                data += struct.pack("B", p1_pos['dir'])
        
        if p2_pos:
            data += struct.pack("BB", p2_pos['x'], p2_pos['y'])
            if 'dir' in p2_pos:
                data += struct.pack("B", p2_pos['dir'])
        
        if game_over:
            data += struct.pack("B", winner)
        
        shots_added = shots_added or []
        data += struct.pack("B", len(shots_added))
        for shot in shots_added:
            data += struct.pack(
                DeltaStatePacket.SHOT_ADD_FORMAT,
                shot['x'], shot['y'], shot['dir'], shot['range'], shot['owner']
            )
        
        shots_removed = shots_removed or []
        data += struct.pack("B", len(shots_removed))
        for x, y in shots_removed:
            data += struct.pack(DeltaStatePacket.SHOT_REMOVE_FORMAT, x, y)
        
        return data
    
    @staticmethod
    def unpack(data):
        try:
            offset = 0
            header_size = struct.calcsize(DeltaStatePacket.HEADER_FORMAT)
            
            if len(data) < header_size:
                raise ValueError("Packet too short")
            
            pkt_type, seq, flags = struct.unpack(
                DeltaStatePacket.HEADER_FORMAT,
                data[offset:offset+header_size]
            )
            offset += header_size
            
            result = {
                'seq': seq, 
                'p1': {}, 
                'p2': {}, 
                'shots_added': [], 
                'shots_removed': []
            }
            
            if flags & DeltaStatePacket.FLAG_P1_POS:
                if len(data) < offset + 2:
                    raise ValueError("Missing P1 position")
                x, y = struct.unpack("BB", data[offset:offset+2])
                result['p1']['x'] = x
                result['p1']['y'] = y
                offset += 2
                
                if flags & DeltaStatePacket.FLAG_P1_DIR:
                    if len(data) < offset + 1:
                        raise ValueError("Missing P1 direction")
                    result['p1']['dir'] = struct.unpack("B", data[offset:offset+1])[0]
                    offset += 1
            
            if flags & DeltaStatePacket.FLAG_P2_POS:
                if len(data) < offset + 2:
                    raise ValueError("Missing P2 position")
                x, y = struct.unpack("BB", data[offset:offset+2])
                result['p2']['x'] = x
                result['p2']['y'] = y
                offset += 2
                
                if flags & DeltaStatePacket.FLAG_P2_DIR:
                    if len(data) < offset + 1:
                        raise ValueError("Missing P2 direction")
                    result['p2']['dir'] = struct.unpack("B", data[offset:offset+1])[0]
                    offset += 1
            
            result['game_over'] = bool(flags & DeltaStatePacket.FLAG_GAME_OVER)
            if result['game_over']:
                if len(data) < offset + 1:
                    raise ValueError("Missing winner")
                result['winner'] = struct.unpack("B", data[offset:offset+1])[0]
                offset += 1
            
            if len(data) < offset + 1:
                raise ValueError("Missing shot add count")
            shot_add_count = struct.unpack("B", data[offset:offset+1])[0]
            offset += 1
            
            shot_size = struct.calcsize(DeltaStatePacket.SHOT_ADD_FORMAT)
            for _ in range(shot_add_count):
                if len(data) < offset + shot_size:
                    raise ValueError("Incomplete shot data")
                x, y, dir, range, owner = struct.unpack(
                    DeltaStatePacket.SHOT_ADD_FORMAT,
                    data[offset:offset+shot_size]
                )
                result['shots_added'].append({
                    'x': x, 'y': y, 'dir': dir, 
                    'range': range, 'owner': owner
                })
                offset += shot_size
            
            if len(data) < offset + 1:
                raise ValueError("Missing shot remove count")
            shot_remove_count = struct.unpack("B", data[offset:offset+1])[0]
            offset += 1
            
            remove_size = struct.calcsize(DeltaStatePacket.SHOT_REMOVE_FORMAT)
            for _ in range(shot_remove_count):
                if len(data) < offset + remove_size:
                    raise ValueError("Incomplete shot remove data")
                x, y = struct.unpack(
                    DeltaStatePacket.SHOT_REMOVE_FORMAT,
                    data[offset:offset+remove_size]
                )
                result['shots_removed'].append((x, y))
                offset += remove_size
            
            return result
        except Exception as e:
            print(f"Error unpacking delta state: {e}")
            return None

class PingPacket:
    """Connection monitoring"""
    FORMAT = "!BxHI"
    SIZE = struct.calcsize(FORMAT)
    
    @staticmethod
    def pack(seq, timestamp):
        return struct.pack(PingPacket.FORMAT, PKT_PING, seq, timestamp)
    
    @staticmethod
    def pack_pong(seq, timestamp):
        return struct.pack(PingPacket.FORMAT, PKT_PONG, seq, timestamp)
    
    @staticmethod
    def unpack(data):
        if len(data) < PingPacket.SIZE:
            raise ValueError("Packet too short")
        
        pkt_type, seq, timestamp = struct.unpack(
            PingPacket.FORMAT, data[:PingPacket.SIZE]
        )
        return {'type': pkt_type, 'seq': seq, 'timestamp': timestamp}
