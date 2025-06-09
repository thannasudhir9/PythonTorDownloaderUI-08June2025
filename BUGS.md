# Bug Tracker
*Last Updated: 2025-06-09 17:33:23*  
*Note: All bugs are referenced with the format BUG-XXX*

## Open Bugs

### BUG-001: Memory Leak in Torrent Session
- **Priority**: High
- **Status**: Open
- **Affected Version**: All
- **Description**: Memory usage gradually increases during long download sessions
- **Related US/Task**: US-6 (Download Management)
- **Steps to Reproduce**:
  1. Start multiple large downloads
  2. Monitor memory usage over time
- **Expected Behavior**: Stable memory usage
- **Actual Behavior**: Memory usage increases continuously
- **Proposed Solution**: 
  - Implement proper resource cleanup
  - Add memory monitoring
  - Consider session recycling

### BUG-002: Theme Toggle Inconsistency
- **Priority**: Medium
- **Status**: Open
- **Affected Version**: v1.0.0
- **Description**: Theme toggle doesn't persist across page refreshes
- **Related US/Task**: US-10 (Customization)
- **Steps to Reproduce**:
  1. Toggle theme
  2. Refresh page
- **Expected Behavior**: Theme preference should persist
- **Actual Behavior**: Reverts to default theme
- **Proposed Solution**:
  - Store theme preference in localStorage
  - Add server-side preference storage

### BUG-003: File Selection Not Persisting
- **Priority**: Medium
- **Status**: Open
- **Affected Version**: v1.0.0
- **Description**: File selection in torrents resets after page refresh
- **Related US/Task**: US-5 (File Selection)
- **Steps to Reproduce**:
  1. Add new torrent
  2. Select/deselect files
  3. Refresh page
- **Expected Behavior**: File selection should persist
- **Actual Behavior**: Resets to default selection
- **Proposed Solution**:
  - Save selection to database
  - Add client-side caching

## Fixed Bugs
*No fixed bugs to display*

## Bug Reporting Guidelines
1. Check if the bug is already reported
2. Include detailed reproduction steps
3. Specify the version where the bug occurs
4. Add screenshots if applicable
5. Mention any error messages

---
*Document generated automatically - Do not edit manually*
