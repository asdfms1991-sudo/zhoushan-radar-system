"""
轨迹存储模块
用于持久化存储目标轨迹
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional


class TrajectoryStorage:
    """轨迹存储管理器"""
    
    def __init__(self, storage_path: str = "data/trajectories"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, target_id: str) -> Path:
        """获取目标轨迹文件路径"""
        safe_id = target_id.replace('/', '_').replace('\\', '_')
        return self.storage_path / f"{safe_id}.json"
    
    def save_trajectory(self, target_id: str, trajectory_data: dict) -> bool:
        """保存轨迹到JSON文件"""
        try:
            file_path = self._get_file_path(target_id)
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    'target_id': target_id,
                    'trajectory': [],
                    'created_at': datetime.now().isoformat()
                }
            
            data['updated_at'] = datetime.now().isoformat()
            data['trajectory'].append(trajectory_data)
            
            if len(data['trajectory']) > 1000:
                data['trajectory'] = data['trajectory'][-1000:]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except (IOError, json.JSONDecodeError) as e:
            print(f"保存轨迹失败: {e}")
            return False
    
    def load_trajectory(self, target_id: str) -> Optional[dict]:
        """加载轨迹"""
        try:
            file_path = self._get_file_path(target_id)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"加载轨迹失败: {e}")
            return None
    
    def load_trajectory_points(self, target_id: str, last_n: int = None) -> List[dict]:
        """加载轨迹点"""
        data = self.load_trajectory(target_id)
        if not data:
            return []
        
        points = data.get('trajectory', [])
        if last_n:
            return points[-last_n:]
        return points
    
    def list_trajectories(self) -> List[str]:
        """列出所有轨迹ID"""
        try:
            files = self.storage_path.glob("*.json")
            return [f.stem for f in files]
        except (IOError, json.JSONDecodeError) as e:
            print(f"列出轨迹失败: {e}")
            return []
    
    def delete_trajectory(self, target_id: str) -> bool:
        """删除轨迹"""
        try:
            file_path = self._get_file_path(target_id)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except (IOError, json.JSONDecodeError) as e:
            print(f"删除轨迹失败: {e}")
            return False
    
    def get_storage_info(self) -> dict:
        """获取存储信息"""
        try:
            files = list(self.storage_path.glob("*.json"))
            total_size = sum(f.stat().st_size for f in files)
            
            return {
                'path': str(self.storage_path),
                'file_count': len(files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2)
            }
        except (IOError, json.JSONDecodeError) as e:
            return {'error': str(e)}
