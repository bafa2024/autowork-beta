from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from datetime import datetime, timedelta
from sqlalchemy import select, func

from database import init_db, Project, Bid
from config import settings

app = FastAPI(title="AutoWork Dashboard")

@app.on_event("startup")
async def startup():
    global db_engine, db_session
    db_engine, db_session = await init_db(settings.database_url)

@app.on_event("shutdown")
async def shutdown():
    await db_engine.dispose()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AutoWork Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto p-6">
            <h1 class="text-3xl font-bold mb-6">AutoWork Dashboard</h1>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div hx-get="/stats/summary" hx-trigger="load, every 5s" class="bg-white p-4 rounded shadow">
                    Loading stats...
                </div>
            </div>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white p-4 rounded shadow">
                    <h2 class="text-xl font-semibold mb-4">Recent Projects</h2>
                    <div hx-get="/projects/recent" hx-trigger="load, every 10s">
                        Loading projects...
                    </div>
                </div>
                
                <div class="bg-white p-4 rounded shadow">
                    <h2 class="text-xl font-semibold mb-4">Recent Bids</h2>
                    <div hx-get="/bids/recent" hx-trigger="load, every 10s">
                        Loading bids...
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/stats/summary")
async def get_stats():
    """Get summary statistics"""
    async with db_session() as session:
        # Get various stats
        total_projects = await session.scalar(select(func.count(Project.id)))
        today_projects = await session.scalar(
            select(func.count(Project.id))
            .where(Project.created_at > datetime.now() - timedelta(days=1))
        )
        total_bids = await session.scalar(select(func.count(Bid.id)))
        successful_bids = await session.scalar(
            select(func.count(Bid.id)).where(Bid.status == "success")
        )
    
    return f"""
    <div class="grid grid-cols-2 gap-4">
        <div>
            <p class="text-gray-600">Total Projects</p>
            <p class="text-2xl font-bold">{total_projects}</p>
        </div>
        <div>
            <p class="text-gray-600">Today's Projects</p>
            <p class="text-2xl font-bold">{today_projects}</p>
        </div>
        <div>
            <p class="text-gray-600">Total Bids</p>
            <p class="text-2xl font-bold">{total_bids}</p>
        </div>
        <div>
            <p class="text-gray-600">Success Rate</p>
            <p class="text-2xl font-bold">
                {(successful_bids/total_bids*100):.1f}% if total_bids > 0 else "N/A"}
            </p>
        </div>
    </div>
    """

@app.get("/projects/recent")
async def get_recent_projects():
    """Get recent projects"""
    async with db_session() as session:
        result = await session.execute(
            select(Project)
            .order_by(Project.created_at.desc())
            .limit(5)
        )
        projects = result.scalars().all()
    
    html = "<ul class='space-y-2'>"
    for project in projects:
        html += f"""
        <li class="border-b pb-2">
            <p class="font-semibold">{project.title[:50]}...</p>
            <p class="text-sm text-gray-600">
                ${project.budget_min} - ${project.budget_max} | 
                {project.bid_count} bids | 
                {'⭐ Elite' if project.is_elite else 'Normal'}
            </p>
        </li>
        """
    html += "</ul>"
    return HTMLResponse(html)

@app.get("/bids/recent")
async def get_recent_bids():
    """Get recent bids"""
    async with db_session() as session:
        result = await session.execute(
            select(Bid, Project)
            .join(Project, Bid.project_id == Project.project_id)
            .order_by(Bid.created_at.desc())
            .limit(5)
        )
        bids = result.all()
    
    html = "<ul class='space-y-2'>"
    for bid, project in bids:
        status_color = "green" if bid.status == "success" else "red"
        html += f"""
        <li class="border-b pb-2">
            <p class="font-semibold">{project.title[:50]}...</p>
            <p class="text-sm">
                <span class="text-{status_color}-600">{bid.status.upper()}</span> |
                ${bid.amount} |
                {bid.created_at.strftime('%H:%M:%S')}
            </p>
        </li>
        """
    html += "</ul>"
    return HTMLResponse(html)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)