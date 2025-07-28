import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class ExpenseDatabase:
    def __init__(self, db_file: str = "data/expenses.json"):
        self.db_file = db_file
        self.ensure_data_directory()
        self.load_data()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
    
    def load_data(self):
        """Load expenses from JSON file"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                self.data = {
                    'expenses': [],
                    'next_id': 1,
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                self.save_data()
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading data: {e}")
            self.data = {
                'expenses': [],
                'next_id': 1,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self.save_data()
    
    def save_data(self):
        """Save expenses to JSON file"""
        try:
            self.data['last_updated'] = datetime.now().isoformat()
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def get_next_id(self) -> int:
        """Get next available expense ID"""
        next_id = self.data['next_id']
        self.data['next_id'] += 1
        return next_id
    
    def add_expense(self, expense: Dict) -> bool:
        """Add a new expense"""
        try:
            self.data['expenses'].append(expense)
            self.save_data()
            return True
        except Exception as e:
            print(f"Error adding expense: {e}")
            return False
    
    def get_expense_by_id(self, expense_id: int) -> Optional[Dict]:
        """Get expense by ID"""
        for expense in self.data['expenses']:
            if expense['id'] == expense_id:
                return expense
        return None
    
    def get_expenses(
        self,
        city: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get filtered expenses"""
        filtered_expenses = []
        
        for expense in self.data['expenses']:
            # Filter by city
            if city and expense['city'] != city:
                continue
            
            # Filter by category
            if category and expense['category'] != category:
                continue
            
            # Filter by date range
            expense_date = expense['date']
            if start_date and expense_date < start_date:
                continue
            if end_date and expense_date > end_date:
                continue
            
            filtered_expenses.append(expense)
        
        # Sort by date (newest first)
        filtered_expenses.sort(key=lambda x: x['date'], reverse=True)
        return filtered_expenses
    
    def add_document_to_expense(self, expense_id: int, document_info: Dict) -> bool:
        """Add document to expense"""
        try:
            expense = self.get_expense_by_id(expense_id)
            if expense:
                if 'documents' not in expense:
                    expense['documents'] = []
                expense['documents'].append(document_info)
                self.save_data()
                return True
            return False
        except Exception as e:
            print(f"Error adding document to expense: {e}")
            return False
    
    def get_summary_stats(self, expenses: List[Dict]) -> Dict:
        """Calculate summary statistics"""
        stats = {
            'total_expenses': len(expenses),
            'total_rmb': 0,
            'sunil_total_rmb': 0,
            'sunil_total_gbp': 0,
            'shirin_total_rmb': 0,
            'shirin_total_aed': 0,
            'categories': {},
            'cities': {},
            'date_range': {'earliest': None, 'latest': None}
        }
        
        if not expenses:
            return stats
        
        dates = []
        
        for expense in expenses:
            # Total amounts
            stats['total_rmb'] += expense['total_rmb']
            stats['sunil_total_rmb'] += expense['sunil_rmb']
            stats['sunil_total_gbp'] += expense['sunil_gbp']
            stats['shirin_total_rmb'] += expense['shirin_rmb']
            stats['shirin_total_aed'] += expense['shirin_aed']
            
            # Category breakdown
            category = expense['category']
            if category not in stats['categories']:
                stats['categories'][category] = {
                    'count': 0,
                    'total_rmb': 0,
                    'sunil_rmb': 0,
                    'sunil_gbp': 0,
                    'shirin_rmb': 0,
                    'shirin_aed': 0
                }
            
            stats['categories'][category]['count'] += 1
            stats['categories'][category]['total_rmb'] += expense['total_rmb']
            stats['categories'][category]['sunil_rmb'] += expense['sunil_rmb']
            stats['categories'][category]['sunil_gbp'] += expense['sunil_gbp']
            stats['categories'][category]['shirin_rmb'] += expense['shirin_rmb']
            stats['categories'][category]['shirin_aed'] += expense['shirin_aed']
            
            # City breakdown
            city = expense['city']
            if city not in stats['cities']:
                stats['cities'][city] = {
                    'count': 0,
                    'total_rmb': 0
                }
            
            stats['cities'][city]['count'] += 1
            stats['cities'][city]['total_rmb'] += expense['total_rmb']
            
            # Date tracking
            dates.append(expense['date'])
        
        # Date range
        if dates:
            stats['date_range']['earliest'] = min(dates)
            stats['date_range']['latest'] = max(dates)
        
        return stats
    
    def update_expense(self, expense_id: int, updates: Dict) -> bool:
        """Update an existing expense"""
        try:
            for i, expense in enumerate(self.data['expenses']):
                if expense['id'] == expense_id:
                    # Update fields
                    for key, value in updates.items():
                        self.data['expenses'][i][key] = value
                    
                    # Save to file
                    self.save_data()
                    return True
            return False
        except Exception as e:
            print(f"Error updating expense: {e}")
            return False
    
    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense permanently"""
        try:
            original_count = len(self.data['expenses'])
            self.data['expenses'] = [exp for exp in self.data['expenses'] if exp['id'] != expense_id]
            
            if len(self.data['expenses']) < original_count:
                self.save_data()
                return True
            return False
        except Exception as e:
            print(f"Error deleting expense: {e}")
            return False
    
    # Document management
    def get_all_documents(self) -> List[Dict]:
        """Get all uploaded documents"""
        documents = []
        for expense in self.data['expenses']:
            if 'documents' in expense and expense['documents']:
                for doc in expense['documents']:
                    doc_info = {
                        'expense_id': expense['id'],
                        'expense_activity': expense['activity'],
                        'expense_date': expense['date'],
                        'expense_city': expense['city'],
                        **doc
                    }
                    documents.append(doc_info)
        return sorted(documents, key=lambda x: x['uploaded_at'], reverse=True)
    
    def delete_document(self, expense_id: int, filename: str) -> bool:
        """Delete a document from an expense"""
        try:
            for expense in self.data['expenses']:
                if expense['id'] == expense_id:
                    if 'documents' in expense:
                        expense['documents'] = [doc for doc in expense['documents'] if doc['filename'] != filename]
                        self.save_data()
                        return True
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    # Database management and analytics
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        stats = {
            'total_expenses': len(self.data['expenses']),
            'total_amount_rmb': sum(exp['total_rmb'] for exp in self.data['expenses']),
            'sunil_total_gbp': sum(exp['sunil_gbp'] for exp in self.data['expenses']),
            'shirin_total_aed': sum(exp['shirin_aed'] for exp in self.data['expenses']),
            'created_at': self.data.get('created_at'),
            'last_updated': self.data.get('last_updated'),
            'next_id': self.data.get('next_id', 1)
        }
        
        # Categories breakdown
        categories = {}
        for exp in self.data['expenses']:
            cat = exp['category']
            if cat not in categories:
                categories[cat] = {'count': 0, 'total_rmb': 0}
            categories[cat]['count'] += 1
            categories[cat]['total_rmb'] += exp['total_rmb']
        stats['categories'] = categories
        
        # Cities breakdown
        cities = {}
        for exp in self.data['expenses']:
            city = exp['city']
            if city not in cities:
                cities[city] = {'count': 0, 'total_rmb': 0}
            cities[city]['count'] += 1
            cities[city]['total_rmb'] += exp['total_rmb']
        stats['cities'] = cities
        
        # Date range
        if self.data['expenses']:
            dates = [exp['date'] for exp in self.data['expenses']]
            stats['date_range'] = {
                'earliest': min(dates),
                'latest': max(dates)
            }
        
        # Documents count
        total_docs = 0
        for exp in self.data['expenses']:
            if 'documents' in exp:
                total_docs += len(exp['documents'])
        stats['total_documents'] = total_docs
        
        return stats
    
    def export_data(self) -> Dict:
        """Export all data for backup"""
        return {
            'data': self.data,
            'export_timestamp': datetime.now().isoformat(),
            'export_version': '1.0'
        }
    
    def import_data(self, imported_data: Dict) -> bool:
        """Import data from backup (careful - overwrites existing data)"""
        try:
            if 'data' in imported_data:
                self.data = imported_data['data']
                self.save_data()
                return True
            return False
        except Exception as e:
            print(f"Error importing data: {e}")
            return False
    
    def clear_all_data(self) -> bool:
        """Clear all data (dangerous operation)"""
        try:
            self.data = {
                'expenses': [],
                'next_id': 1,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self.save_data()
            return True
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False
