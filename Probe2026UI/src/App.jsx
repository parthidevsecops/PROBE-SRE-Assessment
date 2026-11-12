// src/App.jsx
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

import axios from "axios";

import Chatbot from '@/components/Chatbot';
import logo from '@/assets/images/logo.svg';
import 'bootstrap/dist/css/bootstrap.min.css'

function App() {

    const [userInput, setUserInput] = useState('');
    const [chatLog, setChatLog] = useState([]);
    const [loading, setLoading] = useState(false);

    const [fileInputRef, setFileInputRef] = useState({ current: null });
    const [selectedFile, setSelectedFile] = useState(null);
    const [botStatus, setbotStatus] = useState(null);
    
    // Handle file selection
    const onFileChange = (event) => {
        event.preventDefault();
        if (event.target.files) { 
          setSelectedFile(event.target.files[0]);
        }
    };

    // Effect to load chat history from local storage when the app starts
    useEffect(() => {
        const storedChatLog = localStorage.getItem('chatLog');        
        if (storedChatLog) {
            setChatLog(JSON.parse(storedChatLog));
        }
    }, []);


    // Handle file upload form submission
    const handleUpload = async (event) => {
        event.preventDefault();
        if (!selectedFile) {
            setbotStatus('Please select a file first.');
            return;
        }
        else{
             setLoading(true);

            try {
                // FormData is required for sending binary files via multipart/form-data
                const formData = new FormData();
                formData.append('file', selectedFile);
                setbotStatus('Uploading file...');

            //try {
                const response = await fetch('http://localhost:8000/input', {
                    method: 'POST',
                    body: formData,
                    // Note: Do NOT manually set the Content-Type header when sending FormData.
                    // The browser automatically sets it with the required boundary string.
                });

                const data = await response.json();
                var botfileMessage = null ;

                if (response.ok) {
                    setbotStatus(`Success! File saved as: ${data.filename}`);
                    botfileMessage = { type: 'bot', text: `${data.filename} - ${data.message}`}; //botStatus
                } else {
                    setbotStatus(`Upload failed: ${data.detail || data.errorMessage || 'Unknown error'}`);
                    botfileMessage = { type: 'bot', text: botStatus };                       
                }

                // Update the chat log with the bot's response
                const finalFileChatLog = [...chatLog, botfileMessage];
                setChatLog(finalFileChatLog);

                // Save the updated chat log to local storage for persistence
                localStorage.setItem('chatLog', JSON.stringify(finalFileChatLog)); 

                setSelectedFile(null); // Reset input
                fileInputRef.current.value = null;

            } catch (error) {
                console.error('Upload error:', error);
                setbotStatus('Upload failed. Is the server running?');
            } finally {
                setLoading(false);
            }
           
        }
    };


    // Chat submit
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!userInput.trim()) return; // Don't send empty messages

        const userMessage = { type: 'user', text: userInput };
        const newChatLog = [...chatLog, userMessage];
        setChatLog(newChatLog);
        setUserInput('');
        setLoading(true);

        try {
            // The API call to our FastAPI backend
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_message: userInput }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const botMessage = { type: 'bot', text: data.bot_response };

            // Update the chat log with the bot's response
            const finalChatLog = [...newChatLog, botMessage];
            setChatLog(finalChatLog);

            // Save the updated chat log to local storage for persistence
            localStorage.setItem('chatLog', JSON.stringify(finalChatLog));

        } catch (error) {
            console.error('Error fetching chat response:', error);
            const errorMessage = { type: 'error', text: 'Sorry, something went wrong. Please try again.' };
            setChatLog(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };




    // UI page return
    return (
        <div className="App">

        <table className='table'>
            <thead>
            <tr>            
                <th>
                    <a href='https://www.google.com'><img src={logo} className='w-16' alt='logo'/></a>
                </th>
                <th colSpan='3' className='logoColor'>
                    <p>Welcome to AI Trends! I am powered by the latest technology.</p>
                    <p>Ask me anything about the latest technology trends.</p>                     
                </th>
                <th>
                    <h1>AI Trends</h1>
                </th>               
            </tr>
            </thead>

            <tbody>             
            <tr>
                <td>
                    <form onSubmit={handleUpload} className="file-form">
                        <input
                            type="file"
                            ref={fileInputRef}
                            onInput={onFileChange}
                            //onChange= {onFileChange}
                            placeholder="Choose your file..."
                        />
                        <span> </span>
                        <button type="submit" disabled={loading}>Input for Generation</button>
                    </form> 
                </td>
                <td><p> </p></td>
                <td><p> </p></td>
                <td><button onClick={handleSubmit} disabled={loading}>Recommendations Outcome</button></td>
                <td><button onClick={handleSubmit} disabled={loading}>Roadmap</button></td>
            </tr>

            <tr>
                <td colSpan="5">
                    <div className="chat-window">
                        {chatLog.map((message, index) => (
                            <div key={index} className={`message ${message.type}`}>
                                {message.text}
                            </div>
                        ))}
                        {loading && <div className="message bot">Loading...</div>}
                    </div>
                </td>
            </tr>
            <tr>

            </tr>
            <tr>
                <td colSpan="5">    
                    <form onSubmit={handleSubmit} className="chat-form">
                        <input
                            type="text"
                            value={userInput}
                            onChange={(e) => setUserInput(e.target.value)}
                            placeholder="Type your message..."
                            disabled={loading}
                        />
                        <span> </span>
                        <button type="submit" disabled={loading}>Send</button>
                    </form>            
                </td>             
            </tr>
            <tr><td colSpan="5"></td></tr>
            </tbody>

        </table>
        </div>
    );
}

/*
  return (
    <div className='flex flex-col min-h-full w-full max-w-3xl mx-auto px-4'>
      <header className='sticky top-0 shrink-0 z-20 bg-white'>
        <div className='flex flex-col h-full w-full gap-1 pt-4 pb-2'>
          <a href='https://www.google.com'>
            <img src={logo} className='w-32' alt='logo' />
          </a>
          <h1 className='font-urbanist text-[1.65rem] font-semibold'>AI Trends</h1>
        </div>
      </header>
      <Chatbot />
    </div>
  );
}
*/
/* <td><button onClick={handleSubmit} type="submit" disabled={loading}>Generation</button></td> */

export default App;