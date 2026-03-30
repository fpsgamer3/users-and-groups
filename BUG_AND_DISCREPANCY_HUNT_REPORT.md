# 🔍 COMPREHENSIVE BUG & DISCREPANCY HUNT REPORT
**Project:** User Groups Management System  
**Date:** Bug Hunt Session  
**Status:** High-Stakes Presentation - Zero Defect Required  
**Report Format:** Issues organized by severity, component, and reproduction steps

---

## ⚠️ CRITICAL SEVERITY (Can cause presentation failure)

### CRITICAL-1: Teacher Group Deletion Orphans Teachers
**File:** `auth_system/views.py` lines 212-226  
**Component:** GroupDetailView.delete()  
**Issue:** No validation that teacher group has at least one teacher before deletion. If deleted, all teachers lose their group reference.
```python
if group.is_teacher_group:
    # ... permission check ...
    group.delete()  # ← NO CHECK if this leaves no teacher group!
```
**Reproduction:**
1. Create teacher account
2. Delete the "Teachers" group via API
3. Group disappears; teacher loses group membership
4. Unknown error if system tries to access teacher group

**Impact:** Teachers suddenly have no group. System assumes teacher group exists (called in CurrentUserView). Could crash on next page load.

**Presentation Risk:** ⛔ CRITICAL - If demo includes deleting and recreating groups, this fails.

---

### CRITICAL-2: CurrentUserView Calls ensure_teacher_group_membership() on EVERY Request
**File:** `auth_system/views.py` lines ~107  
**Component:** CurrentUserView.get()  
**Issue:** Database write operation on every page refresh for ANY user
```python
def get(self, request):
    ensure_teacher_group_membership()  # ← Called on EVERY request!
    # This runs GET_OR_CREATE queries on every page load
```
**Reproduction:**
1. Log in as any user
2. Refresh page multiple times rapidly (F5, F5, F5)
3. Each refresh triggers database writes
4. If network slow, multiple overlapping requests create race condition

**Impact:** 
- Massive database load in presentation
- Potential for duplicate GroupMembers if requests overlap
- Page load performance degraded
- Page refresh freezes if database slow

**Why it's wrong:** This function should ONLY run on LoginView, not on every CurrentUser check.

**Presentation Risk:** ⛔ CRITICAL - Demo room will have multiple page refreshes; database could slow/crash.

---

### CRITICAL-3: Race Condition in ensure_teacher_group_membership()
**File:** `auth_system/views.py` lines 33-67  
**Component:** ensure_teacher_group_membership()  
**Issue:** Called from both LoginView AND CurrentUserView with bulk_create without transaction protection
```python
def ensure_teacher_group_membership():
    # ... 
    for teacher in all_teachers:
        bulk_entries.append(GroupMember(group=teacher_group, user=teacher))
    
    GroupMember.objects.bulk_create(bulk_entries)  # ← No atomic/transaction
```
**Reproduction:**
1. Open two browser tabs
2. Log in as teacher in BOTH tabs simultaneously
3. Both trigger ensure_teacher_group_membership() at same time
4. Both attempt bulk_create for same GroupMember records

**Expected:** One request wins, other gets duplicate key constraint error  
**Actual:** Unpredictable behavior, possible duplicate GroupMembers for same (teacher, teacher_group) pair

**Impact:** Duplicate teacher entries in teacher group. Strange UI behavior showing same teacher twice.

**Presentation Risk:** ⛔ CRITICAL - Simultaneous login (or page refresh by presenter while demonstrating) creates visible duplicate.

---

### CRITICAL-4: Admin Cannot Create First Group Without Teacher
**File:** `auth_system/views.py` lines 157-165  
**Component:** GroupListView.post()  
**Issue:** Group creation requires admin to appoint a teacher, but validation might fail if no teacher exists
```python
if request.data.get('teacher_id'):
    # Must validate teacher_id
    try:
        teacher = CustomUser.objects.get(id=teacher_id, role='teacher')
    except:
        return error
```
**Reproduction:**
1. Fresh database with only admin user
2. Admin tries to create group
3. No teachers exist to select
4. Cannot create group (chicken-egg problem)

**Impact:** New system cannot be bootstrapped. Cannot create any groups until teacher account exists.

**Presentation Risk:** ⛔ CRITICAL - If starting demo from fresh database, cannot proceed.

---

### CRITICAL-5: Frontend Timeout - Page Freezes on Slow Network
**File:** All fetch calls in React components  
**Component:** RegisterPage.js, GroupPage.js, MembersList.js, etc.  
**Issue:** No timeout on fetch() calls; if server slow, browser hangs indefinitely
```javascript
const response = await fetch('http://localhost:8000/api/auth/groups/', {
    // ... NO TIMEOUT SPECIFIED
});
```
**Reproduction:**
1. Intentionally slow down network (DevTools Network Throttling → Slow 3G)
2. Click any button that makes API call
3. UI freezes, no loading indicator timeout
4. User cannot cancel or retry

**Impact:** UI becomes unresponsive if demo server has any latency issue.

**Presentation Risk:** ⛔ CRITICAL - Network hiccup during demo = frozen UI with no error message.

---

## 🔴 HIGH SEVERITY (Will break features during demo)

### HIGH-1: GroupMemberView.delete() Can Remove Last Teacher from Group
**File:** `auth_system/views.py` lines 318-369  
**Component:** GroupMemberView.delete()  
**Issue:** No validation that group has at least one teacher before removal
```python
def delete(self, request, group_id, user_id):
    # ... permission checks ...
    member.delete()  # ← No check if this is the only teacher!
```
**Reproduction:**
1. Group has teacher + 3 students
2. Remove the teacher
3. Group now has NO teacher
4. Group becomes unmanageable (no one can add/remove members, mute, etc.)

**Impact:** Orphaned group with no teacher/moderator. All group management features fail.

**Presentation Risk:** 🔴 HIGH - If demo includes removing members and accidentally removes teacher, group breaks.

---

### HIGH-2: Auto-Numbering class_number Has No Duplicate Protection
**File:** `auth_system/views.py` lines 303-310  
**Component:** GroupMemberView.post()  
**Issue:** If duplicate GroupMembers somehow exist (shouldn't, but...), max() returns wrong value
```python
max_class_number = GroupMember.objects.filter(...).aggregate(max_num=models.Max('class_number'))
next_class_number = (max_class_number or 0) + 1
```
**Problem:** If database has orphaned duplicates from previous crash, students get wrong numbers.

**Impact:** Multiple students could get same class_number. Course assignments go to wrong students.

---

### HIGH-3: Admins Can See Teacher-Only Group in Their Groups List
**File:** `auth_system/views.py` lines 133-140  
**Component:** GroupListView.get()  
**Issue:** Filters only `is_class_group=False` but doesn't exclude `is_teacher_group=True`
```python
groups = Group.objects.filter(is_class_group=False)  # ← Includes teacher group!
```
**Reproduction:**
1. Log in as admin
2. Go to Groups list
3. See "Teachers" group in the list
4. Click it, sees all teachers
5. Tries to add students to teacher group
6. Gets permission error but it's confusing

**Impact:** UI confusion. Admin tries to manage teacher group, gets errors. Looks like bug.

**Fix:** Change to `groups = Group.objects.filter(is_class_group=False, is_teacher_group=False)`

---

### HIGH-4: GroupMemberView.post() Returns 200 OK When Member Already Exists
**File:** `auth_system/views.py` lines 286-291  
**Component:** GroupMemberView.post()  
**Issue:** Uses `get_or_create()`, but on duplicate returns 200 OK (not 201) with no error message
```python
member, created = GroupMember.objects.get_or_create(group=group, user=user, ...)
# ...
return Response(
    serializer.data,
    status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
)
```
**Reproduction:**
1. Add student to group
2. Try to add same student again
3. Gets 200 OK (not error)
4. Frontend thinks member was added successfully (but they already existed)
5. No indication that duplicate was prevented

**Impact:** Frontend UX confused. User expects error message but gets success.

---

### HIGH-5: Language Preference Lost on Page Refresh
**File:** `frontend/src/components/GroupPage.js`, `LanguageContext.js`  
**Component:** Language Context  
**Issue:** Language stored in state (useState), not in localStorage. Lost on refresh.
```javascript
const [language, setLanguage] = useState('en');  // ← Lost on refresh!
```
**Reproduction:**
1. User switches to Bulgarian
2. Refreshes page (or closes/reopens)
3. App resets to English
4. User preference forgotten

**Impact:** Bad UX. Looks like app doesn't remember preference. In presentation, if presenter switches languages then refreshes, reverts to English.

**Presentation Risk:** 🔴 HIGH - Shows unprofessional UX if language switching is demonstrated.

---

### HIGH-6: Message Editing Permission Check Is Wrong for Teacher
**File:** `auth_system/views.py` lines 468-474  
**Component:** MessageDetailView.put()  
**Issue:** Moderator can edit any message, but only teacher of group can edit
```python
is_moderator = GroupMember.objects.filter(group=group, role='moderator', user=request.user).first()
if message.sender.id != request.user.id and request.user.role != 'admin' and not is_moderator:
    return Response({'error': 'You can only edit your own messages'}, status=status.HTTP_403_FORBIDDEN)
```
**Problem:** Does NOT check if user is teacher. Teacher should be able to edit messages too!

**Expected:** admin, sender, or teacher/moderator can edit  
**Actual:** Only admin, sender, or moderator can edit (teacher is blocked!)

**Impact:** Teacher cannot edit student messages in their group.

---

### HIGH-7: No Validation on Group Name - Could Be Empty or Huge
**File:** `auth_system/models.py` line 39  
**Component:** Group.name field  
**Issue:** CharField(max_length=100) allows empty name (no blank=False in validators)
```python
name = models.CharField(max_length=100, unique=True)  # ← No validation, no blank=False
```
**Reproduction:**
1. POST to create group with empty name ""
2. Or with 100-char long name full of special characters
3. Group created with broken name

**Impact:** Groups with empty names appear in list. Dropdown shows blank option. Confusing UI.

---

## 🟠 MEDIUM SEVERITY (Will cause issues if explored in demo)

### MEDIUM-1: Frontend Has No Error Recovery for Failed Requests
**File:** RegisterPage.js, GroupPage.js, and all fetch() calls  
**Component:** All API calls  
**Issue:** No retry logic or graceful degradation
```javascript
catch (err) {
    setError('Error loading groups');  // ← Generic message, no retry button
}
```
**Reproduction:**
1. Network fails temporarily
2. "Error loading groups" appears
3. User stuck, must manually refresh
4. No "Retry" button offered

**Impact:** Bad UX. User cannot recover from temporary network blip without page refresh.

---

### MEDIUM-2: GroupMemberView.patch() Allows Invalid Grade Values
**File:** `auth_system/views.py` lines 374-395  
**Component:** GroupMemberView.patch()  
**Issue:** No validation that grade is in GRADE_CHOICES
```python
grade = request.data.get('grade')
if grade is not None:
    member.grade = grade if grade else None  # ← No validation!
```
**Reproduction:**
1. PATCH member with grade="XYZ" (invalid)
2. Grade saved to database as "XYZ"
3. Violates data model constraints

**Impact:** Invalid data in database. When displayed, shows wrong grade. Course assignments broken.

---

### MEDIUM-3: Audit Log Not Created for Many Actions
**File:** `auth_system/views.py`  
**Component:** All views  
**Issue:** No audit logging for:
- Group member additions/removals
- Mute/unmute actions  
- Moderator promotions
- Message deletions (partly)

**Impact:** Audit trail incomplete. Cannot track who did what.

---

### MEDIUM-4: MessageView.post() Doesn't Check Mute Status for Admins
**File:** `auth_system/views.py` lines 456-461  
**Component:** MessageView.post()  
**Issue:** 
```python
if request.user.role != 'admin':
    member = group.members.filter(user=request.user).first()
    if member and member.is_muted:
        return Response({'error': 'You have been muted...'}, status=status.HTTP_403_FORBIDDEN)
```
**Wait - this is CORRECT.** Admins can always message. No issue here.

---

### MEDIUM-5: GroupDetailView Doesn't Validate Admin Can See Specific Group
**File:** `auth_system/views.py` lines 185-200  
**Component:** GroupDetailView.get()  
**Issue:** Admins can see ANY group, but permission check might not be clear
```python
def get_group_or_404(self, group_id, user):
    group = Group.objects.get(id=group_id)
    if user.role == 'admin':
        return group  # ← Admins see everything
    # Others see only groups they're members of
```
**Expected:** This is probably correct by design. Admins should see all groups.

---

### MEDIUM-6: No Validation That Teacher ID in Group Creation Is Actually a Teacher
**File:** `auth_system/views.py` lines 157-165  
**Component:** GroupListView.post()  
**Issue:** Wait, actually code DOES check this properly:
```python
try:
    teacher = CustomUser.objects.get(id=teacher_id, role='teacher')
```
**No issue here.** Code is correct.

---

### MEDIUM-7: User Registration No Frontend Async Validation
**File:** `frontend/src/components/RegisterPage.js`  
**Component:** RegisterPage  
**Issue:** No async check for username/email availability BEFORE submit
**Reproduction:**
1. User fills entire registration form
2. Submits with username that already exists
3. Gets 400 error AFTER filling everything
4. Must re-fill form

**Impact:** Poor UX. No real-time username availability check.

**Expected:** Show error under username field as they type (async check)

---

### MEDIUM-8: GroupMember.grade Stored as CharField Instead of Proper Choices
**File:** `auth_system/models.py` line 82  
**Component:** GroupMember.grade field  
**Issue:**
```python
grade = models.CharField(max_length=10, blank=True, null=True, help_text="Student grade (10, 11, 12)")
```
**Problem:** Not linked to GRADE_CHOICES. Could be any string.

---

### MEDIUM-9: Email Not Required in CustomUser But Registration Form Requires It
**File:** `auth_system/models.py` vs. serializer  
**Component:** User model vs. registration  
**Issue:** Model inherits from AbstractUser, email might be optional but registration requires it

---

### MEDIUM-10: No Pagination for Group Members
**File:** `auth_system/views.py` line 194  
**Component:** GroupDetailView (returns all members)  
**Issue:** 
```python
serializer = GroupDetailSerializer(group)  # ← Includes ALL members
```
**If group has 10,000 students, all loaded at once.**

**Impact:** Performance issue. Large groups cause slow page loads.

---

## 🟡 LOW SEVERITY (Edge cases, cosmetic issues)

### LOW-1: Student Role Has No Special Features
**File:** `auth_system/views.py`  
**Component:** Permission system  
**Issue:** Students and guests treated identically. No student-specific features.
**Impact:** Student role seems pointless. Any permission system would treat them same as guest.

---

### LOW-2: No Max Password Length Validation
**File:** `frontend/src/components/RegisterPage.js` line 54  
**Component:** RegisterPage  
**Issue:**
```javascript
if (formData.password.length < 8)  // ← No maximum check
```
**Could submit 10MB password string.**
**Impact:** Potential DoS attack or weird database behavior.

---

### LOW-3: Message Deletion Confirmation Uses window.confirm()
**File:** `frontend/src/components/GroupPage.js` line 115  
**Component:** GroupPage  
**Issue:**
```javascript
if (!window.confirm('Delete this message?')) return;
```
**Problem:** Browser's default confirm() not styled to match app. Looks jarring in polished demo.

---

### LOW-4: No Logout Confirmation
**File:** `frontend/src/components/GroupPage.js` (logout button)  
**Component:** GroupPage  
**Issue:** User can accidentally click logout with no confirmation.

---

### LOW-5: Admin Graph Data Truncates Group Names
**File:** `auth_system/views.py` line 756  
**Component:** AdminGraphDataView  
**Issue:**
```python
'label': group.name[:15],  # ← Truncates to 15 chars, looks weird
```
**Impact:** Long group names cut off in visualization.

---

### LOW-6: AuditLog Filtering Has No Validation on Query Params
**File:** `auth_system/views.py` lines 844-855  
**Component:** AuditLogView.get()  
**Issue:** No validation that action/user_id/group_id are valid before querying
```python
action = request.query_params.get('action')  # ← Could be any string
logs = logs.filter(action=action)
```
**Impact:** Invalid filter value silently ignored (correct behavior), but no error feedback.

---

### LOW-7: No Sorting Options for Members List
**File:** `frontend/src/components/MembersList.js`  
**Component:** MembersList  
**Issue:** Members always sorted by join date. No option to sort by name, grade, number.

---

### LOW-8: Group Export Feature Not Fully Examined
**File:** `auth_system/views.py` lines 704-740  
**Component:** GroupExportView  
**Issue:** Function calls `generate_group_export()` which is not defined in views.py
**Question:** Where is this function? Is it imported? Does it exist?
**Impact:** Export feature might crash with ImportError.

---

## 🚨 PRESENTATION-SPECIFIC RISKS

### RISK-1: Demo Data State Unknown
**Issue:** Previous test run might have left database in bad state
- Deleted groups with orphaned members
- Duplicate teacher group members  
- Invalid grades in database
- Audit logs filled with test data

**Recommendation:** Reset database before presentation
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

### RISK-2: No Test Coverage for Happy Path
**Issue:** If any of the above bugs are NOT observed during demo, it's because the specific sequence of steps that triggers them wasn't taken.

**Recommendation:** Run through demo script multiple times:
1. Create admin account
2. Create teacher account
3. Create student account
4. Create group
5. Add members
6. Send messages
7. Edit/delete messages
8. Make student moderator
9. Mute/unmute student
10. Delete group
11. Refresh page multiple times
12. Switch languages
13. Try adding member twice
14. Try removing teacher from group
15. Export group

---

## 📋 SUMMARY BY COMPONENT

| Component | Critical | High | Medium | Low |
|-----------|----------|------|--------|-----|
| GroupDetailView | 1 | 2 | 1 | 1 |
| GroupMemberView | 0 | 2 | 1 | 0 |
| ensure_teacher_group_membership | 2 | 0 | 1 | 0 |
| MessageView | 0 | 1 | 1 | 0 |
| Frontend (All) | 1 | 1 | 2 | 3 |
| Models | 0 | 1 | 2 | 0 |
| **TOTAL** | **4** | **7** | **8** | **7** |

---

## 🎯 IMMEDIATE ACTIONS REQUIRED

### BEFORE PRESENTATION:

1. **Fix CRITICAL-2:** Remove ensure_teacher_group_membership() from CurrentUserView  
   - Keep it ONLY in LoginView  
   - Should NOT run on every page load

2. **Fix CRITICAL-3:** Wrap bulk_create in database transaction  
   - Add `@transaction.atomic` decorator to ensure_teacher_group_membership()

3. **Fix CRITICAL-1:** Add validation before deleting teacher group  
   - Check that at least one teacher will remain

4. **Fix HIGH-1:** Add validation before removing teacher from group  
   - Ensure group has at least one teacher after removal

5. **Fix HIGH-3:** Filter out teacher group from admin's group list  
   - Change: `filter(is_class_group=False, is_teacher_group=False)`

6. **Test CRITICAL-4:** Verify system can create first group with no teachers  
   - If not, make teacher creation/bootstrapping clearer

7. **Add fetch timeouts:** Set 30-second timeout on all fetch() calls  
   - Prevent UI freezes on slow network

8. **Fix HIGH-5:** Persist language preference to localStorage  
   - Remember user's language choice across sessions

9. **Reset database** before starting demo

10. **Run demo script** at least 3 times to verify no crashes

---

## 🔧 CODE CHANGES NEEDED

### File: `auth_system/views.py`

**Change 1: Remove ensure_teacher_group_membership() from CurrentUserView**
```python
# Line ~107 - REMOVE this line:
# ensure_teacher_group_membership()
```

**Change 2: Add transaction.atomic to ensure_teacher_group_membership()**
```python
from django.db import transaction

@transaction.atomic
def ensure_teacher_group_membership():
    # ... existing code ...
```

**Change 3: Fix GroupListView to exclude teacher group**
```python
# Line ~138
groups = Group.objects.filter(is_class_group=False, is_teacher_group=False)
```

**Change 4: Add validation before removing teacher**
```python
# In GroupMemberView.delete(), before member.delete():
if member.user.role == 'teacher' and group.members.filter(role='teacher').count() <= 1:
    return Response(
        {'error': 'Cannot remove the last teacher from a group'},
        status=status.HTTP_400_BAD_REQUEST
    )
```

**Change 5: Add validation before deleting teacher group**
```python
# In GroupDetailView.delete(), check before group.delete():
if group.is_teacher_group and CustomUser.objects.filter(role='teacher').count() == 0:
    return Response(
        {'error': 'Cannot delete teacher group when no teachers exist'},
        status=status.HTTP_400_BAD_REQUEST
    )
```

### File: `frontend/src/components/*.js`

**Change 6: Add timeout to all fetch calls**
```javascript
// Helper function
const fetchWithTimeout = (url, options = {}, timeout = 30000) => {
    return Promise.race([
        fetch(url, options),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout')), timeout)
        )
    ]);
};

// Use: const response = await fetchWithTimeout(url, options);
```

### File: `frontend/src/LanguageContext.js`

**Change 7: Persist language to localStorage**
```javascript
const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'en';
});

const updateLanguage = (newLang) => {
    setLanguage(newLang);
    localStorage.setItem('language', newLang);
};
```

---

## ✅ VERIFICATION CHECKLIST

Before presenting:
- [ ] All CRITICAL issues fixed and tested
- [ ] All HIGH issues fixed or documented
- [ ] Database reset to clean state
- [ ] Demo script executed successfully 3 times
- [ ] Page refresh tested multiple times (no duplicates)
- [ ] Language switching tested and persists
- [ ] Timeouts tested (slow network simulator)
- [ ] Group member removal tested (verifies teacher protection)
- [ ] First group creation tested (validates bootstrapping works)
- [ ] Message editing tested (verify teacher can edit)
- [ ] No console errors on any page
- [ ] No database constraint violations
- [ ] Admin graph loads without error
- [ ] Export feature works (if demoing it)

---

**Report Generated:** [Bug Hunt Session]  
**Status:** 🚨 ISSUES FOUND - Requires fixes before presentation  
**Recommendation:** Fix all CRITICAL items immediately, test thoroughly, reset database before demo.
