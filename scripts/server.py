import asyncio
import websockets
from twitchio.ext import commands
from collections import deque
import time
import re
import random
import json
import aioftp

# Configuration variables
OAUTH_TOKEN = 'HIDDEN'  # Replace with your OAuth token
CHANNEL = 'sensai_sol'    # Replace with your channel name
WEBSOCKET_PORT = 8766
# QUESTION_TIMEOUT = 90  # seconds to wait for UE5 response
FILLER_TIMEOUT = 15  # seconds to wait before using filler question

# Moderation settings
BLOCKED_WORDS = {'nigger', 'nigga', 'kys'}
MIN_QUESTION_LENGTH = 10
MAX_QUESTION_LENGTH = 300

# Local File Path for Questions
LOCAL_QUESTIONS_FILE = "questions.txt"

class QuestionQueue:
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque()
        self.current_question = None
        self.waiting_for_response = False
        self.last_filler_questions = set()
        self.ready_time = 0

    async def load_questions_from_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f]
            return questions
        except FileNotFoundError:
            print(f"Error: Questions file not found at {filepath}")
            return []
        except Exception as e:
            print(f"Error loading questions from file: {e}")
            return []

    def add_question(self, question, author):
        self.queue.append({"question": question, "author": author, "timestamp": time.time()})

    def get_next_question(self):
        if not self.queue and len(self.last_filler_questions) >= len(self.bot.filler_questions):
            self.last_filler_questions.clear()

        if not self.queue:
            available_questions = [q for q in self.bot.filler_questions if q not in self.last_filler_questions]
            if not available_questions:
                self.last_filler_questions.clear()
                available_questions = self.bot.filler_questions

            if available_questions:
                question = random.choice(available_questions)
                self.last_filler_questions.add(question)
                return {"question": question, "author": "AI", "timestamp": time.time()}
            else:
                return None

        return self.queue.popleft()

class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(token=OAUTH_TOKEN, prefix='!', initial_channels=[CHANNEL])
        self.question_queue = QuestionQueue(self)
        self.connected_clients = set()
        self.filler_questions = []

    def is_question_suitable(self, question: str) -> bool:
        if not (MIN_QUESTION_LENGTH <= len(question) <= MAX_QUESTION_LENGTH):
            return False
        if any(word in question.lower() for word in BLOCKED_WORDS):
            return False
        if sum(1 for c in question if c.isupper()) / len(question) > 0.5:
            return False
        if len(re.findall(r'[!?]{2,}', question)) > 0:
            return False
        return True

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print("Loading questions from local file...")
        self.filler_questions = await self.question_queue.load_questions_from_file(LOCAL_QUESTIONS_FILE)
        print(f"Loaded {len(self.filler_questions)} filler questions.")
        print('Starting question processing loop...')
        self.process_questions_task = asyncio.create_task(self.process_questions())
        print('Question processing loop started')

    async def event_message(self, message):
        if message.author.name.lower() == self.nick.lower():
            return
        if message.content.lower().startswith('!q '):
            question = message.content[3:].strip()
            if self.is_question_suitable(question):
                self.question_queue.add_question(question, message.author.name)
                print(f'New question from {message.author.name}: {question}')
            else:
                print(f'Unsuitable question rejected from {message.author.name}: {question}')

    async def process_questions(self):  # Simplified Process Questions
        while True:
            if not self.question_queue.has_active_connection:
                await asyncio.sleep(1)
                continue
            await asyncio.sleep(1)

    async def broadcast_question(self, question_data):
        if not self.connected_clients:
            return

        message = json.dumps(question_data)
        print(f"Sending to UE5: {message}")

        for client in set(self.connected_clients):
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                self.connected_clients.remove(client)
            except Exception as e:
                print(f'Error sending message: {e}')
                self.connected_clients.remove(client)

    async def send_next_question(self, filler=False):
        if self.question_queue.waiting_for_response:
            print("Already waiting for a response, not sending another question.")
            return

        if filler:
            print("\nQueue empty, sending filler question")
        elif self.question_queue.queue:
            print("\nSending next question from queue")
        else:
            print("No questions available to send.")
            return

        next_question = self.question_queue.get_next_question()

        if next_question:
            await self.broadcast_question(next_question)
            self.question_queue.current_question = next_question
            self.question_queue.waiting_for_response = True
            self.question_queue.ready_time = time.time()
            print("Question sent, waiting for response")

class WebSocketServer:
    def __init__(self, bot):
        self.bot = bot

    async def handler(self, websocket):
        self.bot.connected_clients.add(websocket)
        self.bot.question_queue.has_active_connection = True
        print("New WebSocket client connected - waiting for initial Ready message")
        try:
            async for message in websocket:
                print(f"Received from UE5: {message}")
                if message == "Ready":
                    print("\n=== UE5 is ready for next question ===\n")
                    self.bot.question_queue.waiting_for_response = False
                    if self.bot.question_queue.ready_time == 0: #If this is the first ready command
                        self.bot.question_queue.ready_time = time.time() #Set the ready time
                        if not self.bot.question_queue.queue: #Check if queue is empty
                            if time.time() - self.bot.question_queue.ready_time >= FILLER_TIMEOUT: #Check if filler timeout is reached
                                await self.bot.send_next_question(True) #Send filler question
                        else:
                            await self.bot.send_next_question() #Send normal question
                    else: #Not the first ready command
                        if not self.bot.question_queue.queue: #Check if queue is empty
                            if time.time() - self.bot.question_queue.ready_time >= FILLER_TIMEOUT: #Check if filler timeout is reached
                                await self.bot.send_next_question(True) #Send filler question
                        else:
                            await self.bot.send_next_question()

        except websockets.exceptions.ConnectionClosed:
            print("Client connection closed")
        except Exception as e:
            print(f'WebSocket error: {e}')
        finally:
            self.bot.connected_clients.remove(websocket)
            if not self.bot.connected_clients:
                self.bot.question_queue.has_active_connection = False
                print("All clients disconnected - pausing question processing")

async def main():
    bot = TwitchBot()
    ws_server = WebSocketServer(bot)
    server = await websockets.serve(ws_server.handler, "127.0.0.1", WEBSOCKET_PORT)
    print(f"WebSocket server started on port {WEBSOCKET_PORT}")

    try:
        bot_task = asyncio.create_task(bot.start())
        await asyncio.Future()  # Keep the server running
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        server.close()
        await server.wait_closed()
        await bot.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot stopped due to error: {e}")
