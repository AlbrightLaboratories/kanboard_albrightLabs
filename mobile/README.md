# Kanboard Mobile

React Native mobile application for Kanboard AlbrightLabs.

## Features

- **Board Navigation**: Swipe between columns (Backlog → Groomed → In Progress → Validation → Done)
- **Story Cards**: View story details with priority, labels, and status indicators
- **Agent-in-Comments**: @mention AI agents to get assistance and trigger automated work
- **Semantic Colors**: Red (failure/money loss), Yellow (warning), Green (success/working)
- **Dashboard Colors**: Blue, White, Gold, Black theme
- **Offline Support**: Stories cached locally for offline viewing
- **Push Notifications**: Get notified of story updates

## Color Scheme

| Color | Meaning |
|-------|---------|
| Red | Failure, serious event warning, loss of money |
| Yellow | Warning that may or may not impact performance |
| Green | Money making, everything is working, success |
| Blue | Primary brand color (dashboard) |
| White | Background and clean areas |
| Gold | Accent and highlights |
| Black | Text and borders |

## Agent-in-Comments

Mention an agent in story comments to get AI assistance:

```
@claude Can you help fix this failing test?
```

The agent will:
1. Receive your comment with full story context
2. Respond in the thread
3. When ready to execute, mark with `[READY_TO_EXECUTE]`
4. Upon approval, run code in a sandboxed pod
5. Post results back as comments
6. Create PRs for successful changes

## Project Structure

```
mobile/
├── src/
│   ├── components/
│   │   ├── StoryCard.tsx      # Story card display
│   │   └── AgentComments.tsx  # Agent-in-comments feature
│   ├── screens/
│   │   └── BoardScreen.tsx    # Main board with swipe navigation
│   ├── theme/
│   │   ├── colors.ts          # Color scheme definitions
│   │   └── index.ts           # Theme exports
│   ├── hooks/                 # React hooks
│   ├── navigation/            # Navigation config
│   └── services/              # API and background services
├── __tests__/                 # Test files
├── package.json
└── README.md
```

## Shared Code

The `shared/` directory contains code shared between web and mobile:

- `shared/types/` - TypeScript interfaces (Story, Agent, Worker, etc.)
- `shared/api/` - API client for Kanboard
- `shared/utils/` - Standardized response types and helpers

## Development

```bash
# Install dependencies
npm install

# Start Metro bundler
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android

# Run tests
npm test
```

## Acceptance Criteria

| ID | Description | Status |
|----|-------------|--------|
| MOB-01 | React Native project initializes for iOS and Android | pending |
| MOB-02 | BoardScreen renders with swipe navigation between columns | pending |
| MOB-03 | StoryCard displays title, priority, labels, and status indicators | pending |
| MOB-04 | AgentComments allows @mentions to trigger agent responses | pending |
| MOB-05 | Color scheme applies: red=failure, yellow=warning, green=success | pending |
| MOB-06 | Dashboard uses blue/white/gold/black color scheme | pending |
| MOB-07 | Pull-to-refresh updates story list from API | pending |
| MOB-08 | Story modal opens with full details and edit capability | pending |
| MOB-09 | Offline mode caches stories in AsyncStorage | pending |
| MOB-10 | Push notifications work on iOS and Android | pending |
