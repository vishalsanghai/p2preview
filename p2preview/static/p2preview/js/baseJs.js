function logout() {
  $.ajax({
    url: '/api/v1/logout/', //the page containing php script
    type: 'GET', //request type
    beforeSend: function(request) {
      request.setRequestHeader('TOKEN', getCookie('token'));
    },
    success: function(result) {
      console.log('vishwesh');
      document.cookie = "token=; path=/";
      $(location).attr('href', '/')
    }
  });
}