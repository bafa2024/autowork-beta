# SDLC Analysis Integration

## Overview

The Auto SDLC Service has been successfully integrated into the AutoWork Project Management Dashboard. This integration allows you to automatically analyze project descriptions and generate comprehensive Software Development Life Cycle (SDLC) documents including:

- **Project Analysis**: Type detection, complexity assessment, technology identification
- **Software Requirements Specification (SRS)**: Functional and non-functional requirements
- **System Design Document**: Architecture, components, data models, API endpoints
- **Implementation Plan**: Phases, tasks, timeline, resource allocation

## Features

### 🔍 **Smart Project Analysis**
- Automatically detects project type (web app, mobile app, API, etc.)
- Estimates complexity and development hours
- Identifies required technologies and frameworks
- Extracts key features and potential risks

### 📄 **Document Generation**
- **SRS Document**: Complete requirements specification with user stories
- **Design Document**: System architecture and technical specifications
- **Implementation Plan**: Detailed project timeline and task breakdown

### 🤖 **AI-Powered Analysis**
- Supports multiple AI providers (OpenAI, Anthropic, Google Gemini)
- Intelligent feature extraction from project descriptions
- Context-aware technology recommendations

### 📤 **Export Capabilities**
- Export documents in JSON or Markdown format
- Automatic file generation with timestamps
- Professional document formatting

## How to Use

### 1. **Access the SDLC Analysis Page**
1. Start the API server: `python project_management_api.py`
2. Open your browser and go to: `http://127.0.0.1:5001`
3. Click on "SDLC Analysis" in the navigation menu

### 2. **Enter Project Information**
- **Project Title**: Give your project a descriptive name
- **Project Description**: Provide detailed requirements, features, and constraints
- **Budget** (Optional): Set minimum and maximum budget for better estimates
- **AI Provider**: Choose your preferred AI service (OpenAI recommended)

### 3. **Analyze Your Project**
- Click "Analyze Project" button
- Wait for the analysis to complete (usually 10-30 seconds)
- Review the generated results

### 4. **Review Results**
The analysis will provide:

#### **Project Summary**
- Project type and complexity level
- Estimated development hours
- Identified technologies
- Key features list
- Potential risks

#### **SRS Document**
- Project overview and scope
- Functional requirements
- Non-functional requirements
- User stories
- Acceptance criteria

#### **Design Document**
- System architecture
- Component breakdown
- Data models
- API endpoints
- Technology stack
- Security considerations

#### **Implementation Plan**
- Development phases
- Task breakdown
- Timeline estimates
- Resource allocation
- Milestones

### 5. **Export Documents**
- Click "Export Documents" button
- Choose format (JSON or Markdown)
- Documents will be saved to your local system

## Example Project Description

Here's an example of a good project description:

```
I need a web application for managing a small e-commerce business. 
The system should have:
- Product catalog with categories
- Shopping cart functionality
- User registration and login
- Order management
- Payment integration with Stripe
- Admin dashboard for managing products and orders
- Mobile-responsive design

Technologies preferred: React for frontend, Node.js for backend, PostgreSQL for database.
The project should be completed within 2 months.
```

## API Endpoints

### Analyze Project
```
POST /api/sdlc/analyze
Content-Type: application/json

{
  "project_title": "Project Name",
  "project_description": "Detailed project description...",
  "budget": {
    "minimum": 1000,
    "maximum": 5000
  },
  "ai_provider": "openai"
}
```

### Export Documents
```
POST /api/sdlc/export
Content-Type: application/json

{
  "srs": {...},
  "design": {...},
  "implementation_plan": {...},
  "format": "markdown"
}
```

## Configuration

### Environment Variables
Set these environment variables for AI providers:

```bash
# OpenAI (Recommended)
export OPENAI_API_KEY="your_openai_api_key"

# Anthropic
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# Google Gemini
export GOOGLE_API_KEY="your_google_api_key"
```

### AI Provider Selection
- **OpenAI**: Best for comprehensive analysis and document generation
- **Anthropic**: Good for detailed requirements analysis
- **Google Gemini**: Fast processing, good for basic analysis

## Technical Details

### Project Types Detected
- Web Application
- Mobile Application
- API/Backend Service
- Desktop Application
- Data Science/AI
- Blockchain/Web3
- IoT/Embedded
- Game Development
- Automation/Bots
- E-commerce

### Technology Detection
The system automatically detects:
- **Programming Languages**: Python, JavaScript, Java, C#, PHP, Ruby, Go, Rust, Swift, Kotlin
- **Databases**: MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, Firebase
- **Cloud Platforms**: AWS, Azure, GCP, Heroku, Vercel, Netlify
- **Frameworks**: React, Angular, Vue, Django, Flask, Laravel, Spring Boot

### Complexity Assessment
- **Low**: Simple projects with 1-3 features, <100 hours
- **Medium**: Standard projects with 4-10 features, 100-300 hours
- **High**: Complex projects with 10+ features, >300 hours

## Troubleshooting

### Common Issues

1. **"No API key found"**
   - Set the appropriate environment variable for your AI provider
   - Restart the API server after setting environment variables

2. **"Analysis failed"**
   - Check if your AI provider API key is valid
   - Ensure you have sufficient API credits
   - Try a different AI provider

3. **"Cannot connect to server"**
   - Make sure the API server is running: `python project_management_api.py`
   - Check if port 5001 is available
   - Verify firewall settings

4. **"Export failed"**
   - Ensure the analysis completed successfully first
   - Check file permissions in the output directory
   - Try a different export format

### Performance Tips

1. **Better Project Descriptions**
   - Be specific about features and requirements
   - Include technology preferences
   - Mention constraints and deadlines
   - Provide budget information

2. **AI Provider Selection**
   - Use OpenAI for best results
   - Use Anthropic for detailed analysis
   - Use Gemini for faster processing

3. **Export Optimization**
   - Use Markdown format for better readability
   - Use JSON format for data processing

## Integration with Project Management

The SDLC analysis results can be used to:

1. **Create Project Templates**: Use generated tasks and phases as templates
2. **Estimate Bids**: Use hour estimates for accurate project bidding
3. **Resource Planning**: Use resource allocation for team planning
4. **Risk Management**: Address identified risks in project planning
5. **Client Communication**: Use SRS documents for client discussions

## Future Enhancements

Planned improvements:
- Integration with project management system
- Automatic task creation from implementation plan
- Risk tracking and mitigation strategies
- Cost estimation based on hourly rates
- Integration with version control systems
- Real-time collaboration features

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API server logs for error details
3. Test with a simple project description first
4. Ensure all dependencies are installed

## Dependencies

Required Python packages:
```
flask
flask-cors
requests
sqlalchemy
redis
jinja2
```

Install with:
```bash
pip install flask flask-cors requests sqlalchemy redis jinja2
``` 