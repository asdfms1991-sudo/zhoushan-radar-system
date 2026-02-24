"""
数据导出模块
支持导出为CSV、JSON格式
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class DataExporter:
    """数据导出器"""
    
    def __init__(self, storage_path: str = "data/trajectories"):
        self.storage_path = Path(storage_path)
    
    def export_to_json(self, target_id: str = None, 
                       start_time: str = None,
                       end_time: str = None,
                       output_path: str = None) -> str:
        """
        导出为JSON格式
        
        Args:
            target_id: 目标ID，None表示所有目标
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            output_path: 输出路径
            
        Returns:
            导出文件路径
        """
        from src.history import HistoryPlayer
        
        player = HistoryPlayer(str(self.storage_path))
        
        if target_id:
            # 导出单个目标
            data = player.get_target_history(target_id)
            export_data = {
                'target_id': target_id,
                'exported_at': datetime.now().isoformat(),
                'count': len(data),
                'data': data
            }
        else:
            # 导出所有目标
            all_data = {}
            for file_path in self.storage_path.glob("*.json"):
                tid = file_path.stem
                data = player.get_target_history(tid)
                if data:
                    all_data[tid] = data
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'target_count': len(all_data),
                'data': all_data
            }
        
        # 生成文件名
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_{target_id}" if target_id else "_all"
            output_path = f"data/export_{timestamp}{suffix}.json"
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def export_to_csv(self, target_id: str = None,
                      output_path: str = None) -> str:
        """
        导出为CSV格式
        
        Args:
            target_id: 目标ID
            output_path: 输出路径
            
        Returns:
            导出文件路径
        """
        from src.history import HistoryPlayer
        
        player = HistoryPlayer(str(self.storage_path))
        
        # 收集数据
        rows = []
        
        if target_id:
            data = player.get_target_history(target_id)
            for point in data:
                rows.append({
                    'target_id': target_id,
                    'timestamp': point.get('timestamp', ''),
                    'lat': point.get('lat', 0),
                    'lon': point.get('lon', 0),
                    'speed_knots': point.get('speed_knots', 0),
                    'course_deg': point.get('course_deg', 0)
                })
        else:
            # 所有目标
            for file_path in self.storage_path.glob("*.json"):
                tid = file_path.stem
                data = player.get_target_history(tid)
                for point in data:
                    rows.append({
                        'target_id': tid,
                        'timestamp': point.get('timestamp', ''),
                        'lat': point.get('lat', 0),
                        'lon': point.get('lon', 0),
                        'speed_knots': point.get('speed_knots', 0),
                        'course_deg': point.get('course_deg', 0)
                    })
        
        if not rows:
            return None
        
        # 生成文件名
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_{target_id}" if target_id else "_all"
            output_path = f"data/export_{timestamp}{suffix}.csv"
        
        # 写入CSV
        if rows:
            fieldnames = list(rows[0].keys())
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        return output_path
    
    def generate_report(self, target_id: str = None) -> dict:
        """
        生成数据报告
        
        Args:
            target_id: 目标ID
            
        Returns:
            报告字典
        """
        from src.history import HistoryPlayer
        
        player = HistoryPlayer(str(self.storage_path))
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'target_id': target_id
        }
        
        if target_id:
            stats = player.get_statistics(target_id)
            report.update(stats)
        else:
            stats = player.get_statistics()
            report['total_targets'] = stats.get('total_targets', 0)
            report['total_points'] = stats.get('total_points', 0)
        
        return report


# 测试
if __name__ == '__main__':
    exporter = DataExporter('data/trajectories')
    
    # 测试JSON导出
    # path = exporter.export_to_json()
    # print(f"导出JSON: {path}")
    
    # 测试报告
    report = exporter.generate_report()
    print(f"报告: {report}")
