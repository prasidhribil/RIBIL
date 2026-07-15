const jwt = require('jsonwebtoken');
const token = jwt.sign({id: 'test-user', username: 'test'}, 'f83f59077ce6433b9acf8999d80e39bb15baf21e58cacd3a55e11068b6abc677');
console.log(token);
