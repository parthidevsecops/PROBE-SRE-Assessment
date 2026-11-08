import React from "react";
import CssBaseline from "@material-ui/core/CssBaseline";
import { blue } from "@material-ui/core/colors";
import logo from "../../assets/logo.png";
import {
  Card,
  Container,
  CardHeader,
  Avatar,
  Typography,
  CardContent,
  TextField,
  Grid,
  Box,
  InputAdornment,
  Button,
  FormControlLabel,
  FormGroup,
  // CheckBoxIcon,
  Checkbox,
  // Icon,
} from "@material-ui/core";
import "./LoginPage.css";
import { makeStyles } from "@material-ui/core/styles";
import AccountCircle from "@material-ui/icons/AccountCircle";
import ArrowRightAltIcon from "@material-ui/icons/ArrowRightAlt";
const useStyles = makeStyles({
  card: {
    borderRadius: 20,
  },
  forButton: {
    marginTop: 10,
    fontSize: 12,
    padding: "0px",
    margin: 0,
    lineHeight: 1.5,
    boxShadow: "none",
  },
  forrmGroup: {
    // marginLeft: 2,
  },
  text: {
    paddingLeft: 2,
    color: blue,
  },
  underline: {
    "&&&:before": {
      borderBottom: "none",
    },
    "&&:after": {
      borderBottom: "none",
    },
  },
});
const LoginPage = () => {
  const [state, setState] = React.useState({
    checked: true,
  });
  const classes = useStyles();
  const handleChange = (event) => {
    setState({ ...state, [event.target.name]: event.target.checked });
  };
  return (
    <div className="loginPage">
      <CssBaseline />
      <Box p={2} />

      <Container maxWidth="sm" style={{ height: "50vh", width: "90vw" }}>
        <Box p={3} />

        <Card className={classes.card}>
          <Box p={1} />
          <Grid container justify="center">
            <CardHeader
              avatar={
                <Avatar aria-label="recipe" className="avatar">
                  <img src={logo} alt="logo"></img>
                </Avatar>
              }
            />
          </Grid>
          <Grid container justify="center">
            <CardContent>
              {" "}
              <Grid container justify="center">
                <Typography variant="h6" gutterBottom>
                  Welcome to DigiCon
                </Typography>
              </Grid>
              <Box p={1} />
              <form noValidate autoComplete="off">
                <Grid container justify="center">
                  <TextField
                    id="outlined-basic"
                    name="username"
                    label="Username"
                    variant="outlined"
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <AccountCircle />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Box p={1.8} />
                <Grid container justify="center">
                  <TextField
                    id="outlined-basic"
                    name="password"
                    label="Password"
                    variant="outlined"
                    type="password"
                    helperText="Password length should be >=8"
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <AccountCircle />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
              </form>
              <Box p={2} />
              <Grid container item xs={12} justify="center">
                <Grid item xs={7}>
                  <FormGroup row>
                    <FormControlLabel
                      control={
                        <Checkbox
                          className={classes.forrmGroup}
                          checked={state.checked}
                          onChange={handleChange}
                          name="checked"
                          color="primary"
                        />
                      }
                      label="Keep me logged in"
                    />
                  </FormGroup>
                </Grid>

                <Grid item xs={5}>
                  <Button size="small" className={classes.forButton}>
                    {/* <p> */}
                    <u> Forgot Password?</u>
                    {/* </p> */}
                  </Button>
                </Grid>
              </Grid>
              <Box p={1} />
              <Grid container justify="center">
                <Button
                  style={{ width: "50vw" }}
                  variant="contained"
                  color="primary"
                  endIcon={
                    <ArrowRightAltIcon
                      className={classes.buttonIcon}
                    ></ArrowRightAltIcon>
                  }
                >
                  Login
                </Button>
              </Grid>
              <Box p={1} />
              <Grid container justify="center">
                <p>Don't have an account yet?</p>

                <span>
                  {" "}
                  <button className="text">
                    <p>
                      <u>Sign Up</u>
                    </p>
                  </button>
                </span>
              </Grid>
              <Box p={1} />
            </CardContent>
          </Grid>
        </Card>
      </Container>
    </div>
  );
};

export default LoginPage;
