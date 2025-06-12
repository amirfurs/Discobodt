from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import discord
from discord.ext import commands
import threading
import queue

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Discord Bot setup
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables for bot status
bot_ready = False
bot_user = None

# Queue for handling server creation requests
server_creation_queue = queue.Queue()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class DiscordChannel(BaseModel):
    name: str
    type: str  # "text", "voice", "category"
    category: Optional[str] = None
    position: Optional[int] = 0
    permissions: Optional[Dict[str, Any]] = {}

class DiscordRole(BaseModel):
    name: str
    color: Optional[str] = "#000000"
    permissions: Optional[int] = 0
    mentionable: Optional[bool] = True
    hoist: Optional[bool] = False

class DiscordTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    icon_url: Optional[str] = None
    channels: List[DiscordChannel]
    roles: List[DiscordRole]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

class ServerCreationRequest(BaseModel):
    template_id: str
    server_name: str

class ServerCreationResponse(BaseModel):
    success: bool
    server_id: Optional[str] = None
    invite_link: Optional[str] = None
    message: str

# Discord Bot Events
@bot.event
async def on_ready():
    global bot_ready, bot_user
    bot_ready = True
    bot_user = bot.user
    print(f'{bot.user} has logged in to Discord!')
    
    # Start the server creation worker
    asyncio.create_task(server_creation_worker())

# Server creation worker
async def server_creation_worker():
    """Worker to handle server creation requests from queue"""
    while True:
        try:
            if not server_creation_queue.empty():
                request_data = server_creation_queue.get()
                template = request_data['template']
                server_name = request_data['server_name']
                result_queue = request_data['result_queue']
                
                try:
                    result = await create_discord_server_internal(template, server_name)
                    result_queue.put(result)
                except Exception as e:
                    error_result = ServerCreationResponse(
                        success=False,
                        message=f"Worker error: {str(e)}"
                    )
                    result_queue.put(error_result)
                    
            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
        except Exception as e:
            print(f"Error in server creation worker: {e}")
            await asyncio.sleep(1)

# Discord Bot Functions
async def create_discord_server_internal(template: DiscordTemplate, server_name: str) -> ServerCreationResponse:
    """Internal function to create a Discord server"""
    try:
        if not bot_ready:
            return ServerCreationResponse(
                success=False,
                message="Discord bot is not ready. Please try again."
            )

        # Create the guild (server)
        try:
            guild = await bot.create_guild(name=server_name)
        except discord.HTTPException as e:
            if e.status == 403:
                return ServerCreationResponse(
                    success=False,
                    message="Bot doesn't have permission to create servers. Please check bot permissions."
                )
            else:
                return ServerCreationResponse(
                    success=False,
                    message=f"Discord API error: {str(e)}"
                )
        except Exception as e:
            return ServerCreationResponse(
                success=False,
                message=f"Error creating guild: {str(e)}"
            )
        
        # Wait a moment for the guild to be fully created
        await asyncio.sleep(2)
        
        # Create roles first
        created_roles = {}
        for role_data in template.roles:
            if role_data.name.lower() != "@everyone":  # Skip @everyone role
                try:
                    color_value = int(role_data.color.replace("#", ""), 16) if role_data.color else 0
                    role = await guild.create_role(
                        name=role_data.name,
                        color=discord.Color(color_value),
                        permissions=discord.Permissions(permissions=role_data.permissions or 0),
                        mentionable=role_data.mentionable,
                        hoist=role_data.hoist
                    )
                    created_roles[role_data.name] = role
                except Exception as e:
                    print(f"Error creating role {role_data.name}: {e}")

        # Create categories and channels
        created_categories = {}
        
        for channel_data in template.channels:
            try:
                if channel_data.type == "category":
                    category = await guild.create_category(
                        name=channel_data.name,
                        position=channel_data.position or 0
                    )
                    created_categories[channel_data.name] = category
                    
                elif channel_data.type == "text":
                    category = created_categories.get(channel_data.category)
                    await guild.create_text_channel(
                        name=channel_data.name,
                        category=category,
                        position=channel_data.position or 0
                    )
                    
                elif channel_data.type == "voice":
                    category = created_categories.get(channel_data.category)
                    await guild.create_voice_channel(
                        name=channel_data.name,
                        category=category,
                        position=channel_data.position or 0
                    )
            except Exception as e:
                print(f"Error creating channel {channel_data.name}: {e}")

        # Create an invite link
        try:
            # Get the first text channel to create invite
            text_channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
            if text_channels:
                invite = await text_channels[0].create_invite(max_age=0, max_uses=0)
                invite_link = invite.url
            else:
                invite_link = None
        except:
            invite_link = None

        return ServerCreationResponse(
            success=True,
            server_id=str(guild.id),
            invite_link=invite_link,
            message=f"Server '{server_name}' created successfully!"
        )

    except Exception as e:
        return ServerCreationResponse(
            success=False,
            message=f"Unexpected error: {str(e)}"
        )

async def create_discord_server(template: DiscordTemplate, server_name: str) -> ServerCreationResponse:
    """Queue-based server creation function"""
    result_queue = queue.Queue()
    
    # Add request to queue
    server_creation_queue.put({
        'template': template,
        'server_name': server_name,
        'result_queue': result_queue
    })
    
    # Wait for result (with timeout)
    timeout = 60  # 60 seconds timeout
    start_time = asyncio.get_event_loop().time()
    
    while True:
        if not result_queue.empty():
            return result_queue.get()
            
        current_time = asyncio.get_event_loop().time()
        if current_time - start_time > timeout:
            return ServerCreationResponse(
                success=False,
                message="Server creation timed out. Please try again."
            )
            
        await asyncio.sleep(0.1)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Discord Server Creator API", "bot_ready": bot_ready, "bot_user": str(bot_user) if bot_user else None}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/templates/upload")
async def upload_template(file: UploadFile = File(...)):
    """Upload a Discord template JSON file"""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON file")
        
        content = await file.read()
        template_data = json.loads(content.decode('utf-8'))
        
        # Validate and create template object
        template = DiscordTemplate(**template_data)
        
        # Save to database
        template_dict = template.dict()
        await db.discord_templates.insert_one(template_dict)
        
        return {
            "success": True,
            "message": "Template uploaded successfully",
            "template_id": template.id,
            "template_name": template.name
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing template: {str(e)}")

@api_router.get("/templates", response_model=List[DiscordTemplate])
async def get_templates():
    """Get all uploaded templates"""
    templates = await db.discord_templates.find().to_list(1000)
    return [DiscordTemplate(**template) for template in templates]

@api_router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template by ID"""
    template = await db.discord_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return DiscordTemplate(**template)

@api_router.post("/servers/create", response_model=ServerCreationResponse)
async def create_server(request: ServerCreationRequest):
    """Create a Discord server from template"""
    try:
        # Get template from database
        template_data = await db.discord_templates.find_one({"id": request.template_id})
        if not template_data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template = DiscordTemplate(**template_data)
        
        # Create the server
        result = await create_discord_server(template, request.server_name)
        
        # Save server creation log
        if result.success:
            server_log = {
                "id": str(uuid.uuid4()),
                "template_id": request.template_id,
                "server_name": request.server_name,
                "server_id": result.server_id,
                "invite_link": result.invite_link,
                "created_at": datetime.utcnow(),
                "success": True
            }
            await db.created_servers.insert_one(server_log)
        
        return result
        
    except Exception as e:
        return ServerCreationResponse(
            success=False,
            message=f"Error creating server: {str(e)}"
        )

@api_router.get("/servers/created")
async def get_created_servers():
    """Get list of created servers"""
    servers = await db.created_servers.find().sort("created_at", -1).to_list(100)
    return servers

@api_router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a template"""
    result = await db.discord_templates.delete_one({"id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "message": "Template deleted successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Start Discord bot in background"""
    def run_bot():
        try:
            bot.run(os.environ['DISCORD_BOT_TOKEN'])
        except Exception as e:
            print(f"Error starting Discord bot: {e}")
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Give the bot a moment to start
    await asyncio.sleep(2)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    if bot:
        await bot.close()
