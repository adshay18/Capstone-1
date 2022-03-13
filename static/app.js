let $unlikeForm = $('.unlike-form');
let $likeForm = $('.like-form');

async function handleLike(e) {
	e.preventDefault();
	let $form = $(`#${e.target.id}`);

	$form.children().addClass('unlike-form-button');
	$form.children().removeClass('like-form-button');
	$form.addClass('unlike-form');
	$form.removeClass('like-form');

	const imgId = e.target.id.slice(4);

	await axios.post(`/users/like/${imgId}`);
}

async function handleUnLike(e) {
	e.preventDefault();
	let $form = $(`#${e.target.id}`);

	$form.children().addClass('like-form-button');
	$form.children().removeClass('unlike-form-button');
	$form.addClass('like-form');
	$form.removeClass('unlike-form');

	const imgId = e.target.id.slice(4);

	await axios.post(`/users/unlike/${imgId}`);
}

$likeForm.on('submit', handleLike);
$unlikeForm.on('submit', handleUnLike);
