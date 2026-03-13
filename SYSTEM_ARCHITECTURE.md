# System Architecture & Data Model

## UML Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   CustomUser         │
├──────────────────────┤
│ - id (PK)            │
│ - username (UNIQUE)  │
│ - email              │
│ - first_name         │
│ - last_name          │
│ - role (ROLE_CHOICE) │ ◄──── ENUM: admin, teacher, student
│ - password (hashed)  │
│ - created_at         │
└──────────────────────┘
         │
         │ 1:N
         │
    ┌────┴──────────────────────────────────────┐
    │                                            │
    │                                            │
    ▼                                            ▼
┌──────────────┐                    ┌──────────────────────┐
│   Group      │                    │  GroupMember         │
├──────────────┤                    ├──────────────────────┤
│ - id (PK)    │◄─── 1:N ────┐     │ - id (PK)            │
│ - name       │             │     │ - group_id (FK)      │
│ - description           │     │ - user_id (FK)      │
│ - created_by (FK) ──────┘     │ - role (ROLE_CHOICE) │ ◄─ ENUM: admin, teacher, moderator, student, teacher_moderator
│ - created_at │             │ - joined_at          │
│ - updated_at │             │ - is_muted (Boolean) │
└──────────────┘             └──────────────────────┘
    │                                 │
    │ 1:N                             │
    │                                 │
    ▼                                 ▼
┌──────────────┐            ┌──────────────────────┐
│  Message     │            │ Link: User ─→ Group  │
├──────────────┤            ├──────────────────────┤
│ - id (PK)    │            │ Members of groups    │
│ - group_id   │            │ With specific roles  │
│ - sender_id  │            │ & muted status       │
│ - content    │            └──────────────────────┘
│ - created_at │
│ - updated_at │
└──────────────┘

User ─────────────► Group
      (creator)

User ◄─── GroupMember ───► Group
    (via membership)

User ─────────────► Message
    (sender)
```

## Entity Relationships

### User Roles (Global - CustomUser.role)
- **admin**: Full system access, can see all groups and users
- **teacher**: Can create/manage groups, add members
- **student**: Can join groups, send messages

### Group Member Roles (Per-Group - GroupMember.role)
- **admin**: Full control of group (rarely used)
- **teacher**: Group creator, can manage members
- **moderator**: Can mute/kick students, edit/delete messages (but not kick teachers)
- **student**: Regular member, can send messages (if not muted)
- **teacher_moderator**: Teacher promoted to moderator in that group

### Group Types
- **Regular Groups**: Created by teachers, members are students
- **Teacher Groups**: Created by teachers for teacher collaboration

## Data Flow for Visualization

### What the Graph Should Show:

**Nodes:**
1. **User Nodes** (by global role):
   - Admin users (red)
   - Teachers (blue)
   - Moderators (orange) - detected by GroupMember.role containing 'moderator'
   - Students (purple)

2. **Group Nodes** (green):
   - All groups

**Links (Edges):**
1. **User → Group** (membership):
   - Solid line: regular student member
   - Bold line: moderator member
   - Thick bold line: teacher member
   - Dashed line: creator relationship

2. **Visual Indicators:**
   - Node size: Larger for groups, medium for users
   - Line thickness: Indicates role level
   - Line style: Indicates relationship type
   - Color: Indicates role

## Hierarchical Organization for Graph Layout

```
Depth Level:  Left ────────────────────────────────────────► Right

Level 1:      ADMINS (system-wide authority)
              Position: Far left (x: 10%)

Level 2:      TEACHERS (group creators & managers)
              Position: Left-center (x: 25%)

Level 3:      MODERATORS (group helpers, limited authority)
              Position: Center-left (x: 40%)

Level 4:      STUDENTS (regular members)
              Position: Center-right (x: 50%)

Level 5:      GROUPS (destinations/containers)
              Position: Far right (x: 75%)

Vertical:     Spread by role for clustering visualization
```

## Dynamic Changes to Track

When these happen, update both UML and Visualizer:

1. **User Creation/Deletion**
   - New node appears/disappears
   - Placed in appropriate role level

2. **Group Creation/Deletion**
   - New group node appears/disappears
   - On right side (x: 75%)

3. **User Added to Group**
   - New link created: User → Group
   - Link style based on member role

4. **Member Role Changed** (e.g., student → moderator)
   - User node changes color (purple → orange)
   - User moves to moderator level (x: 40%)
   - Link style updates (regular → bold)

5. **User Muted in Group**
   - Link could get dashed border or special styling
   - Visual indicator of muted status

6. **Group Deleted**
   - All member links disappear
   - Group node disappears

7. **User Removed from Group**
   - Specific link disappears
   - No node changes (user may be in other groups)

## Graph Generation Algorithm

### Backend (AdminGraphDataView):
```
1. Fetch all CustomUsers
2. Detect moderators: users with any GroupMember.role = 'moderator'
3. Create nodes:
   - Each user with their role (use 'moderator' if detected)
   - Each group
4. Create links:
   - For each GroupMember: user_id → group_id
   - Link type based on GroupMember.role
   - Add creator links (user created_by → group)
5. Return nodes[] and links[] as JSON
```

### Frontend (D3.js Visualization):
```
1. Receive nodes and links from backend
2. Apply force simulation:
   - forceLink: Creates tension between connected nodes
   - forceManyBody: Repels nodes from each other
   - forceX/forceY: Positions by role (creates hierarchy)
   - forceCollide: Prevents overlap
3. Render:
   - Groups: Show SVG circles with colors
   - Links: Show lines with styles
   - Labels: Show names
4. Enable interactivity:
   - Drag to reposition
   - Zoom/pan
   - Hover for details
```

## Future Enhancements

1. **Filtering**: Show only teachers, only moderators, specific groups
2. **Search**: Highlight user/group by name
3. **Hover Details**: Show role, member count, join date
4. **Animation**: Animate node additions/removals
5. **Real-time Updates**: WebSocket for live changes
6. **Export**: Save graph as image
7. **Statistics**: Show counts by role, groups per user
8. **Muted Indicator**: Visual indicator for muted users
9. **Group Hierarchy**: Show group nesting (if implemented)
10. **Access Control**: Show who can access which groups

## Implementation Notes

### Why This Approach Works:

✅ **Clear Hierarchy**: Users on left, groups on right
✅ **Role Visibility**: Color and position show role instantly
✅ **Relationship Clarity**: Links show membership and authority
✅ **Scalable**: Works with many users/groups
✅ **Intuitive**: Natural left-to-right flow
✅ **Dynamic**: Easy to add/update nodes and links
✅ **Maintainable**: Clear data structure = easy updates

### Performance Considerations:

- Max 100 nodes performs well with D3.js
- For 1000+ nodes, consider:
  - Filtering/clustering by role
  - Showing only active groups
  - Lazy loading larger datasets
  - Server-side clustering
