function increment(id) {
    document.getElementById(id).stepUp();
}
function decrement(id) {
    document.getElementById(id).stepDown();
}
function addToCart(id , url){
    var username = document.getElementById("username").getAttribute('value');
    var name = document.getElementById(id).name
    var quantity = document.getElementById(id).value
    var price = document.getElementById(id + "-price").textContent
    var price = parseInt(price)
    var itemType = document.getElementById(id + "-type").value
    // alert(username)

    // alert(url);
    
    fetch(url,
    {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username:username, name:name, itemType:itemType, quantity:quantity, price:price})
    }).then(res => {
        alert(JSON.stringify(res));
        alert("Add to cart is successful");
    }).catch(err => alert(err));
}