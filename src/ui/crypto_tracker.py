from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
import requests
import json
from datetime import datetime
import traceback

class CryptoTracker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.coins = {
            'bitcoin': {'symbol': 'BTC', 'name': 'Bitcoin'},
            'ethereum': {'symbol': 'ETH', 'name': 'Ethereum'},
            'dogecoin': {'symbol': 'DOGE', 'name': 'Dogecoin'},
            'litecoin': {'symbol': 'LTC', 'name': 'Litecoin'},
            'shiba-inu': {'symbol': 'SHIB', 'name': 'SHIBA INU'}
        }
        self.setup_ui()
        
        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_prices)
        self.timer.start(30000)  # Update every 30 seconds
        
        # Initial price update
        self.update_prices()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Cryptocurrency Price Tracker")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont('Arial', 18, QFont.Bold))
        layout.addWidget(header)
        
        # Last updated label
        self.update_label = QLabel()
        self.update_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.update_label)
        
        # Create price cards grid
        grid_layout = QGridLayout()
        self.price_widgets = {}
        
        row = 0
        col = 0
        for coin_id, coin_data in self.coins.items():
            card = self.create_price_card(coin_data['name'], coin_data['symbol'])
            self.price_widgets[coin_id] = card
            grid_layout.addWidget(card, row, col)
            
            col += 1
            if col > 2:  # 3 cards per row
                col = 0
                row += 1
        
        layout.addLayout(grid_layout)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Prices")
        refresh_btn.clicked.connect(self.update_prices)
        layout.addWidget(refresh_btn)
        
        # Add stretch to bottom
        layout.addStretch()

    def create_price_card(self, name, symbol):
        card = QFrame()
        card.setFrameStyle(QFrame.Box | QFrame.Raised)
        card.setLineWidth(2)
        card.setMinimumSize(200, 150)
        
        layout = QVBoxLayout(card)
        
        # Coin name
        name_label = QLabel(name)
        name_label.setFont(QFont('Arial', 12, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        
        # Symbol
        symbol_label = QLabel(symbol)
        symbol_label.setAlignment(Qt.AlignCenter)
        
        # Price
        price_label = QLabel("Loading...")
        price_label.setFont(QFont('Arial', 14))
        price_label.setAlignment(Qt.AlignCenter)
        
        # 24h change
        change_label = QLabel("")
        change_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(name_label)
        layout.addWidget(symbol_label)
        layout.addWidget(price_label)
        layout.addWidget(change_label)
        
        # Store labels for updating
        card.price_label = price_label
        card.change_label = change_label
        
        return card

    def update_prices(self):
        try:
            # Get prices from CoinGecko API
            coin_ids = ','.join(self.coins.keys())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=aud&include_24hr_change=true"
            
            # Add user-agent to avoid rate limiting
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Check for rate limiting or errors
            if response.status_code == 429:
                error_msg = "API rate limit exceeded. Please try again later."
                print(error_msg)
                if self.parent:
                    self.parent.statusBar().showMessage(error_msg)
                return
                
            if response.status_code != 200:
                error_msg = f"API returned status code {response.status_code}"
                print(error_msg)
                if self.parent:
                    self.parent.statusBar().showMessage(error_msg)
                return
                
            data = response.json()
            print(f"API Response: {data}")  # Debug output
            
            # Check if we got data for all coins
            if not data:
                print("API returned empty response")
                if self.parent:
                    self.parent.statusBar().showMessage("API returned empty response")
                return
                
            # Update each coin's price
            for coin_id, coin_data in data.items():
                if coin_id in self.price_widgets:
                    card = self.price_widgets[coin_id]
                    
                    # Check if 'aud' key exists in response
                    if 'aud' not in coin_data:
                        print(f"Missing 'aud' data for {coin_id}")
                        continue
                    
                    # Format price based on value
                    price = coin_data['aud']
                    if price < 0.01:
                        price_text = f"A${price:.8f}"
                    elif price < 1:
                        price_text = f"A${price:.4f}"
                    else:
                        price_text = f"A${price:,.2f}"
                    
                    card.price_label.setText(price_text)
                    
                    # Update 24h change with color
                    change = coin_data.get('aud_24h_change', 0)
                    change_text = f"{change:.2f}%"
                    card.change_label.setText(change_text)
                    
                    if change > 0:
                        card.change_label.setStyleSheet("color: green")
                    elif change < 0:
                        card.change_label.setStyleSheet("color: red")
                    else:
                        card.change_label.setStyleSheet("")
            
            # Update last updated time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update_label.setText(f"Last Updated: {current_time}")
            
            if self.parent:
                self.parent.statusBar().showMessage("Prices updated successfully")
                
        except requests.exceptions.Timeout:
            error_msg = "Request timed out. Please check your internet connection."
            print(error_msg)
            if self.parent:
                self.parent.statusBar().showMessage(error_msg)
                
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error. Please check your internet connection."
            print(error_msg)
            if self.parent:
                self.parent.statusBar().showMessage(error_msg)
                
        except json.JSONDecodeError as e:
            error_msg = f"Error parsing API response: {str(e)}"
            print(error_msg)
            print(f"Response content: {response.text}")
            if self.parent:
                self.parent.statusBar().showMessage(error_msg)
                
        except Exception as e:
            error_msg = f"Error updating prices: {str(e)}"
            print(error_msg)
            print(f"Exception type: {type(e).__name__}")
            traceback.print_exc()
            if self.parent:
                self.parent.statusBar().showMessage(error_msg)

    def showEvent(self, event):
        # Start timer when widget becomes visible
        self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        # Stop timer when widget is hidden
        self.timer.stop()
        super().hideEvent(event) 