# Project Structure & Architecture

## Overview

**Leav** is a full-stack learning platform with Django REST backend and React frontend. It features group-based messaging, role-based permissions (admin/teacher/student), and a child-friendly mascot interface.

## Directory Structure

```
/Users/saturn/
├── users_and_groups/                    # Main project root
│   ├── manage.py                         # Django management script
│   ├── db.sqlite3                        # SQLite database (8+ seeded users, 3 groups)
│   ├── exports/                          # Generated DOCX export files **NEW**
│   ├── seed_db.py                        # User seeding script
│   ├── seed_groups.py                    # Group and membership seeding script
│   │
│   ├── users_and_groups/                 # Django project config
│   │   ├── settings.py                   # Django settings (CORS, DRF, Auth, Sessions)
│   │   ├── urls.py                       # Main URL routing
│   │   ├── wsgi.py                       # WSGI configuration
│   │   └── asgi.py                       # ASGI configuration
│   │
│   ├── auth_system/                      # Django auth app
│   │   ├── models.py                     # CustomUser, Group, GroupMember, Message
│   │   ├── serializers.py                # DRF serializers for all models
│   │   ├── views.py                      # API endpoints (15+ views with role checks)
│   │   ├── export_utils.py               # DOCX generation utility **NEW**
│   │   ├── urls.py                       # App-level routing
│   │   ├── admin.py                      # Django admin with Group/Member/Message UIs
│   │   ├── apps.py                       # App configuration
│   │   ├── tests.py                      # Unit tests (placeholder)
│   │   ├── migrations/                   # Database migrations
│   │   └── __init__.py
│   │
│   └── frontend/                         # React application (Leav UI)
│       ├── package.json                  # NPM config (React 18, react-scripts)
│       ├── public/
│       │   ├── index.html                # HTML entry point with Leav branding
│       │   ├── logo.png                  # Leav mascot logo (ChatGPT image)
│       │   ├── cog-wheel.png             # Cog wheel icon for manage button **NEW**
│       │   └── favicon.ico               # Browser tab icon
│       ├── src/
│       │   ├── index.js                  # React DOM root
│       │   ├── App.js                    # Main router (Login → Groups)
│       │   ├── App.css                   # App-level styles
│       │   ├── index.css                 # Global styles
│       │   ├── utils/
│       │   │   └── csrf.js               # CSRF token extraction helper
│       │   └── components/
│       │       ├── LoginPage.js          # Login form with Leav logo
│       │       ├── LoginPage.css         # White bg, green theme
│       │       ├── RegisterPage.js       # Registration form
│       │       ├── RegisterPage.css      # White bg, green theme
│       │       ├── GroupPage.js          # Main group messaging UI with export **UPDATED**
│       │       ├── GroupPage.css         # Green gradient header, responsive layout **UPDATED**
│       │       ├── GroupList.js          # Sidebar group buttons + create/delete
│       │       ├── GroupList.css         # Green color palette
│       │       ├── MessageList.js        # Message display with edit/delete **UPDATED**
│       │       ├── MessageList.css       # Message styling with first-letter avatars
│       │       ├── MessageInput.js       # Message composer with mute check
│       │       ├── MessageInput.css      # Input styling
│       │       ├── MembersList.js        # Members panel + mute/kick/moderator UI **UPDATED**
│       │       ├── MembersList.css       # Member cards with role badges **UPDATED**
│       │       ├── AdminVisualization.js # System graph visualization (admin only) **NEW**
│       │       └── AdminVisualization.css # Visualization styling **NEW**
│       └── node_modules/                 # 1302 npm packages
│
├── workspace.code-workspace              # Multi-root VS Code workspace
├── README.md                             # Full setup & deployment guide
├── PROJECT_STRUCTURE.md                  # This file
└── status.sh                             # Server status checker script
```

## Backend Architecture

### Django REST Framework Setup

**Authentication Flow:**
1. User submits username + password to `/api/auth/login/`
2. Credentials validated against CustomUser model
3. User session created (Django session auth)
4. User data returned with role field
5. Frontend receives user and navigates to Groups page
6. Session persists across page reloads via `current-user` endpoint

**Models:**
- `CustomUser` - Extended AbstractUser with role-based access
  - Roles: admin, teacher, student
  - Fields: username, email, first_name, last_name, role, bio, phone, created_at, updated_at

- `Group` - Learning groups/classes
  - Fields: name, description, created_by (FK), created_at, updated_at

- `GroupMember` - Membership with role in group
  - Fields: group (FK), user (FK), role (admin/teacher/student), joined_at
  - Unique constraint: (group, user)

- `Message` - Group messages
  - Fields: group (FK), sender (FK), content, created_at, updated_at

**API Endpoints:**
- `POST /api/auth/register/` - Create new user (student/teacher only)
- `POST /api/auth/login/` - Authenticate user
- `POST /api/auth/logout/` - End session
- `GET /api/auth/current-user/` - Get logged-in user (for session check)
- `GET /api/auth/users/` - List all users
- `GET /api/auth/admin/graph-data/` - Get system visualization data (admin only) **NEW**

- `GET /api/auth/groups/` - List user's groups (or all for admin)
- `POST /api/auth/groups/` - Create group (teacher/admin only)
- `GET /api/auth/groups/<id>/` - Get group details with messages & members
- `DELETE /api/auth/groups/<id>/` - Delete group (creator/admin only)
- `GET /api/auth/groups/<id>/export/` - Export group to DOCX (teacher/moderator/admin only) **NEW**

- `POST /api/auth/groups/<id>/members/` - Add member (teacher/admin only)
- `DELETE /api/auth/groups/<id>/members/<user_id>/` - Remove member (teacher/admin/moderator)
- `POST /api/auth/groups/<id>/members/<user_id>/moderator/` - Toggle moderator role (teacher/admin only)
- `POST /api/auth/groups/<id>/members/<user_id>/mute/` - Toggle mute status (teacher/admin/moderator)

- `GET /api/auth/groups/<id>/messages/` - List group messages
- `POST /api/auth/groups/<id>/messages/` - Send message (member only, blocked if muted)
- `PUT /api/auth/groups/<id>/messages/<msg_id>/` - Edit message (own, admin, or moderator)
- `DELETE /api/auth/groups/<id>/messages/<msg_id>/` - Delete message (own, admin, teacher, or moderator)

**Configuration:**
- CORS enabled for React frontend (localhost:3000)
- CSRF protection with trusted origins
- Session-based authentication with cookie handling
- DRF for REST serialization
- SQLite for development database
- Django admin panel at `/admin` with full model UIs

### Database

**Schema:**
- CustomUser table with role field (ROLE_CHOICES)
- Group table with created_by FK and timestamps
- GroupMember junction with role field
- Message table with sender FK and timestamps
- Indexed by username, email, group names
- All passwords hashed with Django's PBKDF2 hasher

**Sample Data (8+ users, 3 groups):**
```
Teachers:
  john_doe / teacher123
  jane_smith / teacher123
  robert_brown / teacher123

Students:
  alice_student / student123
  bob_student / student123
  testuser123 / test@example.com

Admin:
  admin / admin123

Groups (pre-seeded):
  Mathematics (8 members)
  Physics (8 members)
  English Literature (8 members)
```

## Frontend Architecture

### React Components

**App.js** - Root component with session management
- State: page (login/register/groups), user, loading
- Features:
  - Session check on app load via `current-user` endpoint
  - Cross-tab logout sync via localStorage (auth-event)
  - Visibilitychange listener for tab focus
  - Routes to LoginPage, RegisterPage, or GroupPage
  - CSRF token handling

**LoginPage.js** - Authentication form
- State: username, password, error, loading, user
- Features:
  - Form validation
  - API call to `/api/auth/login/`
  - Error handling and display
  - Demo credentials helper
  - Link to RegisterPage
  - Backend logout on button click

**RegisterPage.js** - User registration
- State: form data (username, email, name, password), error, loading
- Features:
  - Form validation (passwords match, length checks)
  - Role selection (student/teacher, no admin self-assign)
  - API call to `/api/auth/register/`
  - Error/success handling
  - Link back to LoginPage

**GroupPage.js** - Main messaging interface
- State: groups, selectedGroupId, selectedGroup, messages, members, error
- Features:
  - Fetches user's groups on mount
  - Loads group details (messages, members) when selected
  - Sends/deletes messages with role checks
  - Refreshes members after add/remove operations
  - Green header with Leav logo and user info
  - Three main sections: sidebar, messages, members

**GroupList.js** - Group selector sidebar
- Features:
  - Displays all user's groups as avatar buttons
  - Colored group avatars (rotating palette)
  - Teacher/admin can:
    - Create groups (modal form)
    - Delete groups (with confirmation)
  - Refresh button to reload groups
  - Green color theme

**MessageList.js** - Message display
- Features:
  - Shows messages with user avatars (first letter of name)
  - Avatar colors based on username hash
  - Timestamps and sender info
  - Delete button (own message or staff)
  - Supports long messages with word wrap
  - Empty state message

**MessageInput.js** - Message composer
- Features:
  - Text area input
  - Send button with loading state
  - Form submission handling
  - CSRF token inclusion

**MembersList.js** - Member management
- Features:
  - Lists all members with first-letter avatars
  - Role badges (student/teacher/admin)
  - Color-coded by role (red/amber/green)
  - Teacher/admin can:
    - View "Manage" button
    - Add members (modal with non-member user list)
    - Remove members (with confirmation)
  - Modal for member management

**AdminVisualization.js** - System graph visualization (Admin Only) **NEW**
- Features:
  - Interactive D3.js force-directed graph showing all users and groups
  - Nodes represent users (colored by role) and groups (green)
  - Links show membership relationships with line styles:
    - Solid lines: regular members
    - Dashed lines: creator relationships
    - Thick lines: admin/moderator roles
  - Zoom and pan with mouse wheel and drag
  - Drag individual nodes to rearrange
  - Legend showing color mapping for roles
  - Responsive full-screen layout
  - Permission check: admin only (403 error for non-admins)
  - Loads from `/api/auth/admin/graph-data/` endpoint

### Styling & Design

**Color Palette (Green Theme):**
- Primary green: #2dd46f (bright green for accents)
- Dark green: #22a447 (buttons hover, darker text)
- Teal green: #10b981 (secondary accents)
- Mint green: #06d6a0 (highlights)
- White backgrounds, green gradients for headers
- Red/Amber/Green for admin/teacher/student badges

**Responsive Layout:**
- Header: Green gradient with Leav logo, username, logout
- Sidebar: Group list (80px height cards)
- Main area: Messages + Members side-by-side (flexbox)
- Mobile-friendly with media queries
- Smooth transitions and hover effects

**Branding:**
- Leav mascot logo (ChatGPT image) in header and login/register
- Logo as favicon in browser tab
- Consistent font: Segoe UI, system fonts fallback
- Child-friendly, approachable UI design

### API Communication

- Base URL: `http://localhost:8000/api/auth/` (via fetch)
- Content-Type: application/json
- Fetch API with `credentials: 'include'` for cookies
- CSRF token extraction from `csrftoken` cookie, sent as `X-CSRFToken` header
- Error handling: HTTP status checking + JSON response parsing
- Session persisted in browser cookies

## New Features (February 11, 2026)

### Moderator Role Permissions
- **Mute Students**: Moderators can mute individual students per group (not global)
- **Kick Members**: Moderators can remove students from groups
- **Cannot Kick Teachers**: Backend validation prevents moderators from removing teachers
- **Edit/Delete Messages**: Moderators can edit their own messages and delete any message in the group
- **Cannot Delete Groups**: Group deletion restricted to admins and group creators only
- **Mute Indication**: Muted students see a yellow warning box in MessageInput; cannot send messages (403 error if bypassed)

### Group Export System
- **Export Endpoint**: `GET /api/auth/groups/<id>/export/` generates professional DOCX files
- **Who Can Export**: Teachers, moderators, and admins only (students cannot export)
- **Export Contents**:
  - Group overview (name, description, creator, timestamps, member/message counts)
  - Members table (sorted by join date) with names, usernames, roles, and join dates
  - Complete message history with sender info and timestamps
- **File Storage**: Exports saved to `/exports/` folder with naming pattern: `Group_{id}_{name}_{timestamp}.docx`
- **File Format**: Standard DOCX format using python-docx library, compatible with Microsoft Word and LibreOffice

### UI Updates
- **Export Button**: Green button (📄 Export) in group header bar, visible only to authorized users
- **Manage Button Icon**: Replaced emoji with custom cog wheel image (24x24px) for professional appearance
- **Message Controls**: Edit/delete buttons shown for messages owned by moderators or group staff
- **Member Card Actions**: Mute button appears for moderators; remove button appears for moderators with teacher protection

### Admin System Visualization (NEW)
- **Visualization Button**: Purple button (📊 Visualize) in header, admin-only
- **Graph Display**: Interactive D3.js force-directed graph showing:
  - All users in the system (colored by role: red=admin, blue=teacher, purple=student)
  - All groups (green nodes)
  - Membership relationships (lines connecting users to groups)
  - Creator relationships (dashed lines)
  - Admin/moderator roles (thicker lines)
- **Interactivity**:
  - Zoom with mouse wheel
  - Pan by clicking and dragging
  - Drag individual nodes to rearrange
  - Hover effects and node labels
- **Legend**: Color-coded legend showing node type meanings
- **Data Source**: `/api/auth/admin/graph-data/` endpoint with full system data
- **Permission**: Restricted to admins only (returns 403 Forbidden for non-admins)
- **Use Cases**: 
  - System overview for administrators
  - Understand user-group relationships at a glance
  - Identify organizational structure and connections

### Permission Matrix (Updated)

**Admin Actions:**
| Action | Admin |
|--------|-------|
| View System Visualization | ✓ |
| Access Admin Endpoint | ✓ |

**Group Actions:**
| Action | Admin | Teacher | Moderator | Student |
|--------|-------|---------|-----------|---------|
| Create Group | ✓ | ✓ | ✗ | ✗ |
| Delete Group | ✓ | ✓ (own) | ✗ | ✗ |
| Export Group | ✓ | ✓ | ✓ | ✗ |
| Add Members | ✓ | ✓ (own) | ✗ | ✗ |
| Remove Member | ✓ | ✓ (own) | ✓ (not teachers) | ✗ |
| Promote to Moderator | ✓ | ✓ | ✗ | ✗ |

**Message Actions:**
| Action | Admin | Teacher | Moderator | Student |
|--------|-------|---------|-----------|---------|
| Send Message | ✓ | ✓ | ✓* | ✓* |
| Edit Message | ✓ | ✓ (own) | ✓ (any) | ✓ (own) |
| Delete Message | ✓ | ✓ (any) | ✓ (any) | ✓ (own) |

*Only if not muted

**Member Actions:**
| Action | Admin | Teacher | Moderator | Student |
|--------|-------|---------|-----------|---------|
| Mute Student | ✓ | ✓ | ✓ | ✗ |
| View Muted Status | ✓ | ✓ | ✓ | ✗ |

---

## Running the Application

### Prerequisites
- Python 3.13+
- Node.js v18.19.0 (installed in ~/.node/bin)
- Django 6.0.1
- React 18

### Backend Startup
```bash
cd /Users/saturn/users_and_groups
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Frontend Startup
```bash
export PATH="$HOME/.node/bin:$PATH"
cd /Users/saturn/users_and_groups/frontend
npm start
```

Both services run in parallel:
- Django: http://127.0.0.1:8000
- React: http://localhost:3000

## Code Quality

### Python (Django)
- Clean separation of concerns (models, views, serializers)
- No unused imports
- Proper error handling with status codes
- Type hints in serializer validation

### JavaScript (React)
- Functional components (hooks-based)
- No unused imports (cleaned)
- Proper state management with useState
- Error boundaries for API failures
- Loading states for async operations

### CSS
- No duplicate rules
- Organized by component
- Mobile-first responsive design
- Semantic class naming

## Removed/Cleaned Up

✓ Removed old Django template files (login.html attempts)
✓ Removed JSX/template syntax conflicts ({% verbatim %} tags)
✓ Consolidated frontend folder (moved to users_and_groups/frontend)
✓ Reinstalled npm packages (fixed symlink issues)
✓ Removed unused React imports (useState in App.js)
✓ Cleaned up old root-level files

## Multi-Root Workspace

Open `/Users/saturn/workspace.code-workspace` in VS Code to see both:
1. **Backend (Django)** - users_and_groups/
2. **Frontend (React)** - users_and_groups/frontend/

Both folders visible in sidebar for easier navigation and development.

## Performance Notes

- React: 200 OK response time typically < 100ms
- Django API: 405 (expected, POST-only endpoint) when testing GET
- NPM packages: 1302 total, well-managed dependencies
- Database: SQLite suitable for development, ~6 user queries instant

## Security Considerations

- Passwords: PBKDF2 hashing (Django default)
- CORS: Limited to localhost:3000 in development
- Authentication: Session-based (Django default)
- API: AllowAny for register/login, IsAuthenticated for protected endpoints

## Future Enhancements

- [ ] JWT token authentication (replace sessions)
- [ ] Password reset via email
- [ ] User profile management
- [ ] Role-based dashboard views
- [ ] Audit logging
- [ ] Production database (PostgreSQL)
- [ ] Docker containerization
- [ ] CI/CD pipeline
