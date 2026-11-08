import React from "react";
import Link from "@material-ui/core/Link";
import Typography from "@material-ui/core/Typography";
const Copyright = () => {
  return (
    <Typography variant="body2" color="textSecondary" align="center">
      {"Copyright © "}
      <Link color="inherit" href="#">
        Tata Consultancy Services Limited. All Rights Reserved
      </Link>{" "}
      {new Date().getFullYear()}
      {"."}
    </Typography>
  );
};

export default Copyright;
// ©2020 Tata Consultancy Services Limited. All Rights Reserved
