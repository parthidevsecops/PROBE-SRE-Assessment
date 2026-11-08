// import React from "react";
// import ChatBox from "../Components/ChatPage/ChatPageDesktop/ChatBox";
// import ChatBody from "../Components/ChatPage/ChatPageDesktop/ChatBody";
// import { useState, useEffect } from "react";
// import Alert from "react-bootstrap/Alert";
// // import NavBar from "../Components/NavBar/NavBar";
// import NavBarTest from "../Components/NavBar/NavBarTest";
// const ChatPageContainer = () => {
//   const [show, setShow] = useState(true);
//   const [alert, setAlert] = useState(<div></div>);

//   useEffect(() => {
//     setTimeout(() => {
//       setAlert(
//         <Alert variant="success" onClose={() => setShow(false)} dismissible>
//           <Alert.Heading>Magnum Script ran Successfully</Alert.Heading>
//           <p>You can launch Magnum master server on given IP Address</p>
//         </Alert>
//       );
//     }, 1800000);
//   });

//   return (
//     <React.Fragment>
//       {show === true ? alert : <div></div>}
//       <NavBarTest />
//       <ChatBody />
//       <ChatBox />
//     </React.Fragment>
//   );
// };

// export default ChatPageContainer;
