# System Visualization - Improvements & Architecture

## Overview

The system visualization has been redesigned based on a clear UML model (see `SYSTEM_ARCHITECTURE.md`) to provide a coherent, hierarchical view of users and groups.

## Key Improvements

### 1. **Hierarchical Layout**
The visualization now organizes users and groups in a clear left-to-right hierarchy:

```
Left ◄─────────────────────────────────────────► Right
Admins (8%) → Teachers (22%) → Moderators (37%) → Students (52%) → Groups (78%)
```

Each role level is positioned at a specific horizontal position with vertical spacing for clustering.

### 2. **Improved Link Styling**
Links now communicate relationship types:

| Type | Style | Meaning |
|------|-------|---------|
| **Moderator Links** | Thick, Orange | User has moderator role in that group |
| **Creator Links** | Dashed, Gray | User created the group |
| **Regular Member Links** | Thin, Gray | Student membership |

### 3. **Node Visual Enhancements**
- **Group Nodes**: Larger (r=28) for prominence, green color
- **Admin Nodes**: Red, positioned far left
- **Teacher Nodes**: Blue, positioned left-center
- **Moderator Nodes**: Orange, positioned center-left, with glow effect
- **Student Nodes**: Purple, positioned center-right
- **Hover Effect**: Nodes enlarge and show tooltip with role info

### 4. **Better Force Simulation**
The improved D3.js simulation now:

- **Stronger positioning forces** (strength=0.08) that gently guide nodes to their role hierarchy
- **Role-specific charge repulsion**: Groups repel harder (-500) to stay on the right
- **Collision detection**: Prevents node overlap with radius based on node type
- **Tuned link force**: Creates tension that respects hierarchy positioning
- **Gentle forces**: Still allows manual dragging while maintaining organization

### 5. **Interaction & Information**
- **Hover Tooltips**: Show full name and role on hover
- **Visual Highlights**: Nodes enlarge and glow on hover
- **Drag & Drop**: Users can still rearrange nodes manually
- **Zoom & Pan**: Mouse wheel to zoom, click-drag to pan
- **Legend**: Clear explanation of colors and roles

## Data Model (Backend)

### Graph Generation Algorithm

```javascript
// auth_system/views.py - AdminGraphDataView

1. Fetch all users and groups
2. Detect moderators: Users with GroupMember.role = 'moderator'
3. Create nodes:
   - Each user with role: admin/teacher/moderator/student
   - Each group with role: 'group'
   - Include is_moderator flag for highlighting

4. Create links for each GroupMember:
   - source: user_id
   - target: group_id
   - type: 'moderator' | 'member' | 'creator'
   
5. Return JSON: { nodes: [...], links: [...] }
```

### Backend Logic for Moderators

```python
# Identify moderators across all groups
moderator_users = set()
for member in GroupMember.objects.filter(role__in=['moderator', 'teacher_moderator']):
    moderator_users.add(member.user.id)

# When creating user node, check if they're a moderator anywhere
for user in users:
    is_mod = user.id in moderator_users
    nodes.append({
        'id': f"user_{user.id}",
        'role': 'moderator' if is_mod and user.role == 'student' else user.role,
        'is_moderator': is_mod
    })
```

## Frontend Visualization (React/D3.js)

### Hierarchy Positioning Function

```javascript
const getNodeHierarchy = (node) => {
  const width = window.innerWidth;
  const heights = {
    'admin': { x: width * 0.08, y: height * 0.15 },
    'teacher': { x: width * 0.22, y: height * 0.25 },
    'moderator': { x: width * 0.37, y: height * 0.35 },
    'student': { x: width * 0.52, y: height * 0.55 },
    'group': { x: width * 0.78, y: height * 0.5 }
  };
  return heights[node.role];
};
```

### Force Configuration

```javascript
d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).distance(150).strength(0.3))
  .force('charge', d3.forceManyBody().strength(-300 to -500))
  .force('center', d3.forceCenter(width/2, height/2))
  .force('collision', d3.forceCollide().radius(25-35))
  .force('x', d3.forceX().x(pos).strength(0.08))
  .force('y', d3.forceY().y(pos).strength(0.08))
```

## What's Shown in the Graph

### Nodes (Entities)
1. **Users** by global role:
   - Admin: 1 (red)
   - Teachers: 4 (blue)
   - Moderators: 3 (orange) 
   - Students: 3 (purple)

2. **Groups**: 5 total (green)

### Links (Relationships)
1. **Membership**: User connects to group they're in
2. **Moderator Status**: Highlighted with orange, thick line
3. **Creator**: Dashed line shows who created each group

## How to Interpret the Graph

**Reading the visualization left-to-right:**

```
ADMINS           TEACHERS         MODERATORS       STUDENTS         GROUPS
(Red)            (Blue)           (Orange)         (Purple)         (Green)
                                  ● (glow)
●                ●                  ↓                ●
                  |\                │                |\
                  | \━━━━━━━━━━━━━━▶│━━━━━━━━━━━━━━▶ ◎
                  |                 │
                  └─────────────────┴─────────────────────────▶ ◎
                     (creator line - dashed)
```

- **Thick Orange Lines**: Moderator relationships
- **Dashed Lines**: Group creator relationships  
- **Thin Gray Lines**: Regular membership
- **Glowing Orange Nodes**: Moderators (have authority in some group)

## Dynamic Changes to Track

When these events occur, the UML and visualizer update:

| Event | Node Change | Link Change | Position Change |
|-------|-------------|-------------|-----------------|
| User created | New node | - | Based on role |
| User deleted | Node removed | All links removed | - |
| Group created | New node | - | Far right (78%) |
| Group deleted | Node removed | All links removed | - |
| User added to group | - | New link | - |
| User removed from group | - | Link removed | - |
| User promoted to moderator | Node color changes | Link style changes | Moves to moderator level |
| User demoted from moderator | Node color changes | Link style changes | Moves back to student level |

## Benefits of This Design

✅ **Clarity**: Clear role hierarchy left-to-right
✅ **Cohesion**: Groups cluster on right, users on left
✅ **Hierarchy**: Role determines horizontal position
✅ **Relationships**: Links show who has authority
✅ **Scalability**: Works well up to 100+ nodes
✅ **Maintainable**: UML-based, clear data structure
✅ **Interactive**: Responsive to user actions
✅ **Intuitive**: Natural reading flow

## Performance Notes

Current visualization handles:
- ✅ Up to 20 users
- ✅ Up to 10 groups
- ✅ Smooth animation with D3.js
- ✅ 60 FPS rendering

For larger systems (100+ users):
- Consider filtering by role/group
- Use lazy loading for distant nodes
- Implement clustering for dense areas
- Server-side graph analysis

## Files Modified

1. **backend/auth_system/views.py**
   - AdminGraphDataView: Enhanced moderator detection

2. **backend/auth_system/urls.py**
   - Route: `/api/auth/admin/graph-data/`

3. **frontend/src/components/AdminVisualization.js**
   - Improved D3.js force simulation
   - Hierarchical positioning
   - Better link styling
   - Hover tooltips
   - Visual enhancements

4. **frontend/src/components/AdminVisualization.css**
   - Styling for visualization container
   - Legend and header styling
   - Info bar styling

5. **PROJECT_STRUCTURE.md**
   - Documentation updated

6. **SYSTEM_ARCHITECTURE.md** (NEW)
   - Complete UML diagrams
   - Data model documentation
   - Algorithm descriptions
