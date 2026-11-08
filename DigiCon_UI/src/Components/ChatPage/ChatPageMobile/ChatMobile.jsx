import React, { Component } from "react";
import { Redirect } from "react-router-dom";
import SendIcon from "@material-ui/icons/Send";
import axios from "axios";
import apiUrl from "../../../Service/api";
import { animations } from "react-animation";
import Typing from "../../UI/Typing/Typing";
class ChatBox extends Component {
  messagesEndRef = React.createRef(null);
  constructor(props) {
    super(props);

    this.state = {
      // messagesEnd: React.createRef(),
      loggedIn: true,
      show: false,
      msg: "",
      min: false,
      anyIndex: 0,
      typing: false,
      animation: [
        { animation: animations.bounceIn },
        { animation: animations.bounceOut },
      ],
      chat: [],
    };
  }
  scrollToBottom = () => {
    this.messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };
  componentDidMount() {
    const token = localStorage.getItem("token");
    if (token == null) {
      this.setState({
        loggedIn: false,
      });
    }
  }
  componentDidUpdate() {
    if (this.state.show === true) {
      this.scrollToBottom();
      this.inputField.focus();
    }
  }

  onButtonClick = () => {
    this.setState({
      anyIndex: 0,
      show: true,
    });
    if (this.state.min === false) {
      setTimeout(() => {
        this.setState({
          chat: [
            {
              type: "bot",
              Message: "Hi I am DigiCon Bot",
            },
          ],
        });
      }, 1200);
    }

    console.log(this.state.show);
  };

  onChangeValue = (e) => {
    this.setState({
      msg: e.target.value,
    });
  };

  onSendMessgae = (e) => {
    if (this.state.msg !== "") {
      const message = {
        message: this.state.msg,
      };
      const chat = [
        ...this.state.chat,
        {
          type: "user",
          Message: this.state.msg,
        },
      ];
      this.setState({ chat, msg: "", typing: true });
      console.log(`------> ${apiUrl.chatApi}`);
      axios
        .post(apiUrl.chatApi, message)
        .then((response) => {
          console.log(response.data);
          const chat = [
            ...this.state.chat,

            {
              type: "bot",
              Message: response.data.response,
            },
          ];
          this.setState({ chat, typing: false });
        })
        .catch((err) => {
          console.log(err);
          const chat = [
            ...this.state.chat,

            {
              type: "bot",
              Message: `Network Error caused by ${err}`,
            },
          ];
          this.setState({ chat, typing: false });
        });
    }

    document.getElementById("form-reset").reset();
  };

  onKeyPressEvent = (event) => {
    var code = event.keyCode || event.which;
    if (code === 13) {
      this.onSendMessgae(event);
    }

    // event.preventDefault();
  };
  submitHandler(e) {
    e.preventDefault();
  }
  render() {
    if (this.state.loggedIn === false) {
      return <Redirect to="/login" />;
    }
    let chat = this.state.chat.map((i, index) => {
      if (i.type === "bot") {
        return (
          <div
            key={index}
            className="responseContainer"
            style={{ animation: animations.popIn }}
          >
            <div className="replyBot">
              <p>{i.Message}</p>
            </div>
          </div>
        );
      } else {
        return (
          <div
            key={index}
            className="userContainer"
            style={{ animation: animations.popIn }}
          >
            <div className="chatUser">
              <p>{i.Message}</p>
            </div>
          </div>
        );
      }
    });
    let UI = (
      <div
        id="chatwindow"
        className="chatBoxMobile"
        style={this.state.animation[this.state.anyIndex]}
      >
        <div className="msgContainerMobile">
          {chat} <div ref={this.messagesEndRef} />{" "}
          {this.state.typing === true ? <Typing /> : ""}
        </div>

        <form id="form-reset" className="textbox" onSubmit={this.submitHandler}>
          <input
            type="text"
            className="inputfield"
            placeholder="Type a Message....."
            onChange={this.onChangeValue}
            onKeyPress={this.onKeyPressEvent}
            ref={(input) => {
              this.inputField = input;
            }}
          ></input>
          <div className="sendButton" onClick={this.onSendMessgae}>
            <SendIcon />
          </div>
        </form>
      </div>
    );

    return <React.Fragment>{UI}</React.Fragment>;
  }
}

export default ChatBox;
