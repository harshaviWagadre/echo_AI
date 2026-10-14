Frontend for echo (React + Vite)

Run:
  npm install
  npm run dev

The UI includes simple components to talk to the backend:
- ImageCreator -> POST /image/create
- VideoEditor -> POST /video/edit
- Chatbot -> POST /chat

Adjust backend URL in axios calls if the backend runs on a different host/port.